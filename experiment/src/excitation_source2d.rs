use std::fs;
use std::path::PathBuf;

use indicatif::ProgressBar;
use ordered_float::{FloatIsNan, NotNan};
use rand::prelude::*;
use rand_distr::{Normal, Uniform};
use serde::{Deserialize, Serialize};
use serde_json::{from_str, to_string_pretty};

use crate::coord2d::Coord2D;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Excitation2D {
    coord: Coord2D,
    time: NotNan<f64>,
}

impl Excitation2D {
    pub fn new(time: f64, x: f64, y: f64) -> Result<Self, FloatIsNan> {
        let coord = Coord2D::new(x, y)?;
        let time = NotNan::new(time)?;

        Ok(Self { coord, time })
    }

    pub fn time_s(&self) -> f64 {
        self.time.into_inner()
    }

    pub fn into_coord(self) -> Coord2D {
        self.coord
    }

    pub fn to_bytes(self) -> [u8; 24] {
        let mut result: [u8; 24] = [0; 24];
        let (time_bytes, coord_bytes) = result.split_at_mut(8);
        time_bytes.copy_from_slice(&self.time.to_be_bytes());
        coord_bytes.copy_from_slice(&self.coord.to_bytes());

        result
    }

    pub fn from_bytes(time_coord: &[u8]) -> Self {
        if time_coord.len() != 24 {
            panic!("Malformed serialized Excitation2D")
        }

        let time = NotNan::new(f64::from_be_bytes(time_coord[..8].try_into().unwrap())).unwrap();

        let coord = Coord2D::from_bytes(&time_coord[8..]);

        Self { coord, time }
    }
}

pub trait ExcitationSource2D {
    type Params: Serialize;

    /// Get the excitation at index n if it exists
    fn nth(&self, n: usize) -> Option<&Excitation2D>;

    /// Get the next excitation, but don't advance the iterator
    fn peek(&self) -> Option<&Excitation2D>;

    /// Get the next excitation
    fn next(&mut self) -> Option<Excitation2D>;

    fn params(&self) -> Self::Params;
}

#[derive(Debug, Clone)]
struct ExcitationProgressBar(ProgressBar);

impl std::default::Default for ExcitationProgressBar {
    fn default() -> Self {
        ExcitationProgressBar(ProgressBar::new(0))
    }
}

impl std::cmp::PartialEq for ExcitationProgressBar {
    fn eq(&self, other: &ExcitationProgressBar) -> bool {
        self.0.length() == other.0.length()
    }

    fn ne(&self, other: &ExcitationProgressBar) -> bool {
        self.0.length() != other.0.length()
    }
}

#[derive(Serialize, Deserialize, Debug, Clone, PartialEq)]
pub struct PulsedExcitationGaussian2DParams {
    pub spot_fwhm_m: f64,
    pub repetition_rate_hz: f64,
    pub pulse_fwhm_s: f64,
    pub n_excitations: usize,
    pub n_pulses: usize,
}

#[derive(Debug, Clone)]
pub struct PulsedExcitationGaussian2D {
    params: PulsedExcitationGaussian2DParams,
    cursor: usize,
    excitations: Vec<Excitation2D>,
    progress_bar: ExcitationProgressBar,
}

impl std::cmp::PartialEq for PulsedExcitationGaussian2D {
    fn eq(&self, other: &PulsedExcitationGaussian2D) -> bool {
        self.params == other.params
            && self.cursor == other.cursor
            && self.excitations == other.excitations
    }

    fn ne(&self, other: &PulsedExcitationGaussian2D) -> bool {
        self.params != other.params
            || self.cursor != other.cursor
            || self.excitations != other.excitations
    }
}

impl PulsedExcitationGaussian2D {
    fn make_coords(spot_fwhm_m: f64, n_excitations: usize) -> Vec<Coord2D> {
        let std_dev_m = spot_fwhm_m / 2.355;

        let mut rand_iter = rand::rng().sample_iter(Normal::new(0.0, std_dev_m).unwrap());
        (0..n_excitations)
            .into_iter()
            .map(|_| Coord2D::new(rand_iter.next().unwrap(), rand_iter.next().unwrap()).unwrap())
            .collect()
    }

    fn make_times(
        n_excitations: usize,
        n_pulses: usize,
        repetition_rate_hz: f64,
        pulse_fwhm_s: f64,
    ) -> Vec<NotNan<f64>> {
        let mut pulse_idx_rand_iter =
            rand::rng().sample_iter(Uniform::try_from(0..n_pulses).unwrap());

        let std_dev_s = pulse_fwhm_s / 2.355;
        let mut offset_from_pulse_iter =
            rand::rng().sample_iter(Normal::new(0.0, std_dev_s).unwrap());

        let pulse_repetition_period_s = 1.0 / repetition_rate_hz;
        let mut times: Vec<NotNan<f64>> = (0..n_excitations)
            .into_iter()
            .map(|_| {
                NotNan::new(
                    (pulse_idx_rand_iter.next().unwrap() as f64) * pulse_repetition_period_s
                        + offset_from_pulse_iter.next().unwrap(),
                )
                .expect("rand normal distribution generated NaN")
            })
            .collect();
        times.sort();
        times
    }

    pub fn new(params: PulsedExcitationGaussian2DParams) -> Self {
        let excitations: Vec<Excitation2D> =
            Self::make_coords(params.spot_fwhm_m, params.n_excitations)
                .into_iter()
                .zip(Self::make_times(
                    params.n_excitations,
                    params.n_pulses,
                    params.repetition_rate_hz,
                    params.pulse_fwhm_s,
                ))
                .map(|(coord, time)| Excitation2D { coord, time })
                .collect();

        Self {
            progress_bar: ExcitationProgressBar(ProgressBar::new(params.n_excitations as u64)),
            params,
            cursor: 0,
            excitations,
        }
    }

    fn advance_cursor(&mut self) {
        self.cursor += 1;
        self.progress_bar.0.inc(1);
    }

    fn config_path(path: &PathBuf) -> PathBuf {
        let mut result = path.clone();
        result.push("config");
        result.set_extension("json");
        result
    }

    fn excitation_path(path: &PathBuf) -> PathBuf {
        let mut result = path.clone();
        result.push("excitations");
        result
    }

    pub fn write(self, path: &PathBuf) {
        fs::write(
            Self::config_path(path),
            to_string_pretty(&self.params()).unwrap(),
        )
        .expect("failed to write config JSON");

        let excitation_bytes: Vec<u8> = self
            .excitations
            .into_iter()
            .flat_map(|x| x.to_bytes())
            .collect();
        fs::write(Self::excitation_path(path), excitation_bytes)
            .expect("failed to write excitation bytes");
    }

    pub fn read(path: &PathBuf) -> Self {
        let json_str = fs::read_to_string(Self::config_path(path))
            .expect("failed to read config file to string");
        let params: PulsedExcitationGaussian2DParams = from_str(&json_str)
            .expect("failed to parse json string for PulsedExcitationGaussian2d");

        let excitations = fs::read(Self::excitation_path(path))
            .expect("failed to read excitation binary data")
            .chunks_exact(24)
            .map(|slice| Excitation2D::from_bytes(slice))
            .collect::<Vec<_>>();

        Self {
            progress_bar: ExcitationProgressBar(ProgressBar::new(params.n_excitations as u64)),
            params,
            cursor: 0,
            excitations,
        }
    }
}

impl ExcitationSource2D for PulsedExcitationGaussian2D {
    type Params = PulsedExcitationGaussian2DParams;

    fn nth(&self, n: usize) -> Option<&Excitation2D> {
        if n >= self.params.n_excitations {
            None
        } else {
            Some(&self.excitations[n])
        }
    }

    /// Get the next excitation, but don't advance the iterator
    fn peek(&self) -> Option<&Excitation2D> {
        if self.cursor >= self.params.n_excitations {
            None
        } else {
            Some(&self.excitations[self.cursor])
        }
    }

    fn next(&mut self) -> Option<Excitation2D> {
        if self.cursor >= self.params.n_excitations {
            None
        } else {
            let result = Some(self.excitations[self.cursor].clone());
            self.advance_cursor();
            result
        }
    }

    fn params(&self) -> Self::Params {
        self.params.clone()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_pulsed_excitation_gaussian_2d_new() {
        let excitations = PulsedExcitationGaussian2D::new(PulsedExcitationGaussian2DParams {
            spot_fwhm_m: 1.0e-6,
            repetition_rate_hz: 1.0e6,
            pulse_fwhm_s: 100.0e-15,
            n_excitations: 1_000,
            n_pulses: 10,
        });

        assert_eq!(
            excitations.excitations.len(),
            excitations.params.n_excitations
        );

        let tmp_dir = std::env::temp_dir();
        excitations.clone().write(&tmp_dir);
        let rehydrated = PulsedExcitationGaussian2D::read(&tmp_dir);
        assert_eq!(excitations, rehydrated);
    }

    #[test]
    fn test_excitation_2d_serde() {
        let x = Excitation2D::new(1.0, 2.0, 3.0).unwrap();
        let bytes = x.clone().to_bytes();
        let rehydrated = Excitation2D::from_bytes(&bytes);

        assert_eq!(x, rehydrated)
    }
}
