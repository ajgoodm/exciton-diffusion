use std::collections::HashSet;
use std::fs;
use std::path::PathBuf;

use rand::rngs::ThreadRng;
use rand::seq::IndexedRandom;
use rand::Rng;
use rand_distr::{Distribution, Exp, StandardNormal};
use serde::Serialize;
use serde_json::to_string_pretty;

use crate::coord2d::Coord2D;
use crate::excitation_source2d::{Excitation2D, ExcitationSource2D, SplittableExcitationParams};
use crate::exciton::{AnnihilationOutcome, ExcitonBiography, ExcitonParameters};
use crate::utils::random_uniform_zero_to_pi;

enum CriticalEvent {
    NewExcitation(Excitation2D),
    ExcitonsCouldCollide(f64),
    OneExcitonRemains,
    NoExcitonsRemain,
    ZeroRadiusExcitons,
}

struct ExcitonCollection {
    excitons: Vec<Coord2D>,
    cursor: usize, // the next empty index, the number of excitons
    exciton_parameters: ExcitonParameters,
    rng: ThreadRng,
    radiative_decay_distribution: Exp<f64>,
}

impl ExcitonCollection {
    pub fn from_parameters(exciton_parameters: ExcitonParameters) -> Self {
        Self {
            excitons: Vec::new(),
            cursor: 0,
            radiative_decay_distribution: Exp::new(exciton_parameters.radiative_decay_rate_per_s)
                .unwrap(),
            exciton_parameters,
            rng: rand::rng(),
        }
    }

    fn n_excitons(&self) -> usize {
        self.cursor
    }

    /// The minimum distance separating two excitons represented by hard spheres.
    /// Equivalent to the minimum center-to-center distance less 2 radii.
    /// Assumes that no two excitons are overlapping (will panic)
    fn minimum_interexciton_distance_m(&self) -> Option<f64> {
        if self.n_excitons() < 2 {
            return None;
        }

        let mut min_distance = f64::MAX;
        for idx_1 in 0..self.n_excitons() {
            for idx_2 in 0..idx_1 {
                let first = &self.excitons[idx_1];
                let second = &self.excitons[idx_2];

                let distance = first
                    .distance(second)
                    .expect("calculating inter-exciton distance yielded NaN")
                    .into_inner();
                if distance < min_distance {
                    min_distance = distance
                }
            }
        }

        if min_distance <= 2.0 * self.exciton_parameters.exciton_radius_m {
            panic!("We were supposed to eliminate overlapping excitons before calling minimum_interexciton_distance_m")
        }

        Some(f64::abs(
            min_distance - 2.0 * self.exciton_parameters.exciton_radius_m,
        ))
    }

    /// After a time step Δt, a diffusing particle with diffusivity D will move
    /// by a random distance r with probability distribution proportional to exp(-r^2 / 4DΔt).
    // The distance travelled is normally distributed with standard deviation σ = sqrt(2DΔt).
    //
    // When drawing a random distance value, we can make an approximation and assume
    // that the distance will be less than 5σ which should be true for > 99.99994% of random draws
    // https://en.wikipedia.org/wiki/Standard_deviation#Rules_for_normally_distributed_data
    fn time_until_next_plausible_collision(&self) -> Option<f64> {
        if self.exciton_parameters.exciton_radius_m == 0.0 {
            return None;
        }

        match self.minimum_interexciton_distance_m() {
            // the time Δt_0 at which 5σ = 5 * sqrt(2DΔt_0) equals dist
            Some(dist) => {
                // if two excitons move directly toward each other,
                // they each only need to cover half the distance
                Some((dist / 5.0).powi(2) / (2.0 * self.exciton_parameters.diffusivity_m2_per_s))
            }
            None => None,
        }
    }

    pub fn annihilate(&mut self, time_s: f64) -> Vec<ExcitonBiography> {
        let mut excitons_to_remove: HashSet<usize> = HashSet::new();

        if self.n_excitons() < 2 || self.exciton_parameters.exciton_radius_m == 0.0 {
            return Vec::new();
        }

        for idx_1 in 1..self.n_excitons() {
            for idx_2 in 0..idx_1 {
                let first = &self.excitons[idx_1];
                let second = &self.excitons[idx_2];
                let distance = first
                    .distance(second)
                    .expect("calculating inter-exciton distance yielded NaN")
                    .into_inner();

                if distance < 2.0 * self.exciton_parameters.exciton_radius_m {
                    match self.exciton_parameters.annihilation_outcome {
                        AnnihilationOutcome::One => {
                            excitons_to_remove
                                .insert(*[idx_1, idx_2].choose(&mut self.rng).unwrap());
                        }
                        AnnihilationOutcome::Both => {
                            excitons_to_remove.extend([idx_1, idx_2]);
                        }
                    }
                }
            }
        }

        let mut exciton_idx_vec = excitons_to_remove.into_iter().collect::<Vec<_>>();
        exciton_idx_vec.sort();
        exciton_idx_vec
            .into_iter()
            .rev()
            .map(|idx| ExcitonBiography {
                destroyed_at_s: time_s,
                destroyed_at_position: self.remove_exciton(idx),
                decayed_radiatively: false,
            })
            .collect()
    }

    fn diffuse_exciton_at_idx(&mut self, idx: usize, delta_t: f64) {
        let dist = self.capped_diffusion_distance_m(delta_t);
        let angle = random_uniform_zero_to_pi(&mut self.rng);
        let translation_vector = Coord2D::new(angle.cos() * dist, angle.sin() * dist)
            .expect("Calculating diffusion translation vector produced NaN");

        self.excitons
            .get_mut(idx)
            .expect("Tried to translate exciton that does not exist")
            .translate(&translation_vector);
    }

    pub fn diffuse_and_decay(&mut self, time_s: f64, delta_t_s: f64) -> Vec<ExcitonBiography> {
        let mut decayed_exciton_indices_and_dts: Vec<(usize, f64)> = Vec::new();
        for idx in 0..self.n_excitons() {
            let radiative_decay_draw = self.radiative_decay_draw();
            if radiative_decay_draw <= delta_t_s {
                // the exciton decays after diffusing until its death
                self.diffuse_exciton_at_idx(idx, radiative_decay_draw);
                decayed_exciton_indices_and_dts.push((idx, radiative_decay_draw));
            } else {
                // the exciton doesn't decay this time step, but diffuses
                // for the whole time step
                self.diffuse_exciton_at_idx(idx, delta_t_s);
            }
        }

        decayed_exciton_indices_and_dts.sort_by_key(|(idx, _)| *idx);
        decayed_exciton_indices_and_dts
            .into_iter()
            .rev()
            .map(|(idx, dt)| ExcitonBiography {
                destroyed_at_s: time_s + dt,
                destroyed_at_position: self.remove_exciton(idx),
                decayed_radiatively: true,
            })
            .collect()
    }

    pub fn next_critical_event<T: ExcitationSource2D>(
        &self,
        time_s: f64,
        minimum_time_step_s: f64,
        excitation_source: &mut T,
    ) -> CriticalEvent {
        let next_excitation = excitation_source.peek();
        let next_plausible_collision = match self.time_until_next_plausible_collision() {
            Some(delta_t_s) => {
                if delta_t_s < minimum_time_step_s {
                    Some(time_s + minimum_time_step_s)
                } else {
                    Some(time_s + delta_t_s)
                }
            }
            None => None,
        };

        match (next_excitation, next_plausible_collision) {
            (None, None) => {
                if self.n_excitons() == 0 {
                    CriticalEvent::NoExcitonsRemain
                } else if self.n_excitons() == 1 {
                    CriticalEvent::OneExcitonRemains
                } else if self.exciton_parameters.exciton_radius_m == 0.0 {
                    CriticalEvent::ZeroRadiusExcitons
                } else {
                    panic!("Expected 0 or one exciton if there is no new excitation and no chance of inter-exciton collision")
                }
            }
            (Some(_), None) => CriticalEvent::NewExcitation(excitation_source.next().unwrap()),
            (None, Some(collision_time_s)) => CriticalEvent::ExcitonsCouldCollide(collision_time_s),
            (Some(excitation_2d), Some(collision_time_s)) => {
                if excitation_2d.time_s() < collision_time_s {
                    CriticalEvent::NewExcitation(excitation_source.next().unwrap())
                } else {
                    CriticalEvent::ExcitonsCouldCollide(collision_time_s)
                }
            }
        }
    }

    pub fn add_exciton(&mut self, excitation_2d: Excitation2D) {
        if self.cursor >= self.excitons.len() {
            self.excitons.push(excitation_2d.into_coord());
        } else {
            self.excitons[self.cursor] = excitation_2d.into_coord();
        }
        self.cursor += 1;
    }

    /// Try to minimize allocations by moving the last element to idx
    /// and decrementing cursor
    fn remove_exciton(&mut self, idx: usize) -> Coord2D {
        if idx >= self.cursor {
            panic!("Out of bounds error when removing exciton")
        }

        let result = self.excitons[idx].clone();
        self.excitons.swap(idx, self.cursor - 1);
        self.cursor -= 1;

        result
    }

    fn final_decay_event(mut self, time_s: f64) -> ExcitonBiography {
        if self.cursor != 1 {
            panic!(
                "Called final_decay_event but the number of living excitons is {}",
                self.cursor
            )
        }

        let time_to_decay = self.radiative_decay_draw();
        self.diffuse_exciton_at_idx(0, time_to_decay);
        ExcitonBiography {
            destroyed_at_s: time_s + time_to_decay,
            destroyed_at_position: self.excitons[0].clone(),
            decayed_radiatively: true,
        }
    }

    /// Draw from the exponentially decaying probability distribution function
    /// k_R * exp(-k_R * t) where k_R is the radiative decay rate [1/s]
    fn radiative_decay_draw(&mut self) -> f64 {
        self.radiative_decay_distribution.sample(&mut self.rng)
    }

    /// Draw from the standard normal (σ = 1, μ = 0) probability distribution function
    fn standard_normal_draw(&mut self) -> f64 {
        self.rng.sample(StandardNormal)
    }

    /// Draw a random diffusion distance based on the exciton diffusivity
    /// and the provided time step. Always return a distance that is within
    /// 5 standard deviations from the mean (0, the point of origin)
    fn capped_diffusion_distance_m(&mut self, delta_t: f64) -> f64 {
        let standard_normal_draw: f64;
        loop {
            let attempt = self.standard_normal_draw();
            if f64::abs(attempt) <= 5.0 {
                standard_normal_draw = attempt;
                break;
            }
        }

        standard_normal_draw * (0.5 * self.exciton_parameters.diffusivity_m2_per_s * delta_t).sqrt()
    }
}

pub struct SimulationOutput<T: Serialize + SplittableExcitationParams + Clone> {
    exciton_biographies: Vec<ExcitonBiography>,
    excitation_source_params: T,
}

impl<T: Serialize + SplittableExcitationParams + Clone> SimulationOutput<T> {
    pub fn new(exciton_biographies: Vec<ExcitonBiography>, excitation_source_params: T) -> Self {
        Self {
            exciton_biographies,
            excitation_source_params,
        }
    }

    pub fn merge(bits: Vec<Self>) -> Self {
        let excitation_source_params: T = T::merge(
            bits.iter()
                .map(|output| output.excitation_source_params.clone())
                .collect::<Vec<T>>(),
        );
        let exciton_biographies = bits.into_iter().fold(Vec::new(), |mut acc, output| {
            acc.extend(output.exciton_biographies);
            acc
        });
        Self {
            exciton_biographies,
            excitation_source_params,
        }
    }

    pub fn len(&self) -> usize {
        self.exciton_biographies.len()
    }

    fn config_path(path: &PathBuf) -> PathBuf {
        let mut result = path.clone();
        result.push("config");
        result.set_extension("json");
        result
    }

    fn emission_events_path(path: &PathBuf) -> PathBuf {
        let mut result = path.clone();
        result.push("emission_events");
        result
    }

    pub fn write(self, path: &PathBuf) {
        fs::write(
            Self::config_path(path),
            to_string_pretty(&self.excitation_source_params).unwrap(),
        )
        .expect("failed to write config JSON");

        let emission_events_bytes: Vec<u8> = self
            .exciton_biographies
            .into_iter()
            .filter(|x| x.decayed_radiatively)
            .flat_map(|x| x.to_bytes())
            .collect();
        fs::write(Self::emission_events_path(path), emission_events_bytes)
            .expect("failed to write excitation bytes");
    }
}

pub struct Simulation2D<T: ExcitationSource2D> {
    excitation_source: T,
    exciton_parameters: ExcitonParameters,
    minimum_time_step_s: f64,
}

impl<T: ExcitationSource2D> Simulation2D<T> {
    pub fn new(exciton_parameters: ExcitonParameters, excitation_source: T) -> Self {
        Self {
            minimum_time_step_s: Self::min_time_step_from_params(&exciton_parameters),
            excitation_source,
            exciton_parameters,
        }
    }

    /// The minimum time to diffuse one exciton radius
    /// assuming that over a time Δt, an exciton diffuses at most 5σ
    /// where σ = sqrt(2DΔt)
    ///
    /// We can solve for the minimum time using 5 * sqrt(2D * Δt_0) =  R
    /// where Δt_0 is the minimum time, D is the diffusivity, and R is the exciton
    /// radius. This yields:
    ///     Δt_0 = (R / 5)^2 * (1 / (2 * D))
    fn min_time_step_from_params(exciton_parameters: &ExcitonParameters) -> f64 {
        (exciton_parameters.exciton_radius_m / 5.0).powi(2)
            * (1.0 / (2.0 * exciton_parameters.diffusivity_m2_per_s))
    }

    pub fn run(mut self) -> SimulationOutput<T::Params> {
        let mut result = Vec::new();
        let mut excitons = ExcitonCollection::from_parameters(self.exciton_parameters.clone());
        let mut time_s = self
            .excitation_source
            .peek()
            .expect("Started simulation with no exictions")
            .time_s();

        loop {
            result.extend(excitons.annihilate(time_s));
            match excitons.next_critical_event(
                time_s,
                self.minimum_time_step_s,
                &mut self.excitation_source,
            ) {
                CriticalEvent::NewExcitation(excitation_2d) => {
                    // we have to simulate the time up until the new excitation event
                    let delta_t_s = excitation_2d.time_s() - time_s;
                    result.extend(excitons.diffuse_and_decay(time_s, delta_t_s));

                    // set the current time to the excitation instant and
                    // add the exciton to our exciton collection
                    time_s = excitation_2d.time_s();
                    excitons.add_exciton(excitation_2d);
                }
                CriticalEvent::ExcitonsCouldCollide(next_time) => {
                    let delta_t_s = next_time - time_s;
                    result.extend(excitons.diffuse_and_decay(time_s, delta_t_s));
                    time_s = next_time;
                }
                CriticalEvent::OneExcitonRemains => {
                    result.push(excitons.final_decay_event(time_s));
                    break;
                }
                CriticalEvent::NoExcitonsRemain => {
                    break;
                }
                CriticalEvent::ZeroRadiusExcitons => {
                    let delta_t_s = self.exciton_parameters.radiative_decay_rate_per_s.powi(-1);
                    result.extend(excitons.diffuse_and_decay(time_s, delta_t_s));
                    time_s += delta_t_s;
                }
            }
        }

        SimulationOutput::new(result, self.excitation_source.params())
    }
}

#[cfg(test)]
mod tests {
    use crate::excitation_source2d::{
        PulsedExcitationGaussian2D, PulsedExcitationGaussian2DParams,
    };

    use super::*;

    #[test]
    fn test_simulation() {
        let parameters = ExcitonParameters {
            diffusivity_m2_per_s: 6.0e-6,
            radiative_decay_rate_per_s: 1.0e8,
            non_radiative_decay_rate_per_s: 0.0,
            exciton_radius_m: 1.0e-9,
            annihilation_outcome: AnnihilationOutcome::One,
        };

        let excitation_source_params = PulsedExcitationGaussian2DParams {
            spot_fwhm_m: 1.0e-6,
            repetition_rate_hz: 1.0e6,
            pulse_fwhm_s: 100.0e-15,
            n_excitations: 10,
            n_pulses: 10,
        };
        let excitation_source =
            PulsedExcitationGaussian2D::new(excitation_source_params.clone(), false);

        let simulation: Simulation2D<PulsedExcitationGaussian2D> =
            Simulation2D::new(parameters, excitation_source);
        let simulation_output = simulation.run();
        assert_eq!(
            simulation_output.len(),
            excitation_source_params.n_excitations
        ); // all excitations are accounted for

        let tmp_dir = std::env::temp_dir();
        simulation_output.write(&tmp_dir);
    }
}
