use crate::coord2d::Coord2D;
use crate::excitation_source2d::{Excitation2D, ExcitationSource2D};
use crate::exciton::{ExcitonBiography, ExcitonParameters};

enum CriticalEvent {
    NewExcitation(Excitation2D),
    ExcitonsCouldCollide(f64),
    OneExcitonRemains,
    NoExcitonsRemain,
}

struct ExcitonCollection {
    excitons: Vec<Coord2D>,
    cursor: usize, // the next empty index, the number of excitons
    diffusivity_m2_per_s: f64,
    exciton_radius_m: f64,
}

impl ExcitonCollection {
    pub fn new(diffusivity_m2_per_s: f64, exciton_radius_m: f64) -> Self {
        Self {
            excitons: Vec::new(),
            cursor: 0,
            diffusivity_m2_per_s,
            exciton_radius_m,
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

        if min_distance <= 2.0 * self.exciton_radius_m {
            panic!("We were supposed to eliminate overlapping excitons before calling minimum_interexciton_distance_m")
        }

        Some(f64::abs(min_distance - 2.0 * self.exciton_radius_m))
    }

    /// After a time step Δt, a diffusing particle with diffusivity D will move
    /// by a random distance r with probability distribution proportional to exp(-r / 4DΔt).
    // The distance travelled is normally distributed with standard deviation σ = sqrt(2DΔt).
    //
    // When drawing a random distance value, we can make an approximation and assume
    // that the distance will be less than 5σ which should be true for > 99.99994% of random draws
    // https://en.wikipedia.org/wiki/Standard_deviation#Rules_for_normally_distributed_data
    fn time_until_next_plausible_collision(&self) -> Option<f64> {
        match self.minimum_interexciton_distance_m() {
            // the time at which 5σ = sqrt(2DΔt) equals dist
            Some(dist) => Some(dist.powi(2) / (2.0 * self.diffusivity_m2_per_s)),
            None => None,
        }
    }
}

impl ExcitonCollection {
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

    pub fn add_exciton(&mut self) {}

    pub fn remove_exciton(&mut self, idx: usize) {}

    pub fn step(&mut self, dt: f64) {}
}

pub struct Simulation2D<T: ExcitationSource2D> {
    minimum_step_size_s: f64,
    excitation_source: T,
    exciton_parameters: ExcitonParameters,
    living_excitons: Vec<Coord2D>,
}

impl<T: ExcitationSource2D> Simulation2D<T> {
    pub fn run(self) -> Vec<ExcitonBiography> {
        let result = Vec::new();
        result
    }
}
