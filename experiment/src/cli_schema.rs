use std::{path::PathBuf, str::FromStr};

use serde::{Deserialize, Serialize};
use thiserror::Error;

use crate::excitation_source2d::PulsedExcitationGaussian2D;
use crate::exciton::{AnnihilationOutcome, ExcitonParameters};

#[derive(Error, Debug)]
pub enum CLIPathError {
    #[error("The provided path ({0}) does not exist")]
    FileDoesNotExist(String),

    #[error("The provided directory ({0}) does not exist")]
    DirectoryDoesNotExist(String),

    #[error("The provided path ({0}) is a file; expected a directory")]
    ExpectedDirectoryNotFile(String),
}

#[derive(Debug, Clone)]
pub struct ExistingFilePath(pub PathBuf);

impl FromStr for ExistingFilePath {
    type Err = CLIPathError;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        let path = PathBuf::from(s);
        if !path.exists() {
            Err(CLIPathError::FileDoesNotExist(s.to_string()))
        } else {
            Ok(ExistingFilePath(path))
        }
    }
}

#[derive(Debug, Clone)]
pub struct ExistingDirectory(pub PathBuf);

impl FromStr for ExistingDirectory {
    type Err = CLIPathError;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        let path = PathBuf::from(s);
        if !path.exists() {
            Err(CLIPathError::DirectoryDoesNotExist(s.to_string()))
        } else if path.is_file() {
            Err(CLIPathError::ExpectedDirectoryNotFile(s.to_string()))
        } else {
            Ok(ExistingDirectory(path))
        }
    }
}

#[derive(Clone, Deserialize, Serialize)]
pub struct ExcitonParametersInput {
    pub diffusivity_m2_per_s: f64,
    pub radiative_decay_rate_per_s: f64,
    pub exciton_radius_m: f64,
    pub annihilation_outcome: AnnihilationOutcome,
}

impl ExcitonParametersInput {
    pub fn params(&self) -> ExcitonParameters {
        ExcitonParameters {
            diffusivity_m2_per_s: self.diffusivity_m2_per_s,
            radiative_decay_rate_per_s: self.radiative_decay_rate_per_s,
            non_radiative_decay_rate_per_s: 0.0,
            exciton_radius_m: self.exciton_radius_m,
            annihilation_outcome: self.annihilation_outcome.clone(),
        }
    }
}

impl FromStr for ExcitonParametersInput {
    type Err = serde_json::Error;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        serde_json::from_str(s)
    }
}

#[derive(Clone, Deserialize, Serialize)]
pub struct PulsedExcitationInput {
    spot_fwhm_m: f64,
    repetition_rate_hz: f64,
    pulse_fwhm_s: f64,
    n_excitations: usize,
    n_pulses: usize,
}

impl PulsedExcitationInput {
    pub fn excitation_source(&self) -> PulsedExcitationGaussian2D {
        PulsedExcitationGaussian2D::new(
            self.spot_fwhm_m,
            self.n_excitations,
            self.n_pulses,
            self.repetition_rate_hz,
            self.pulse_fwhm_s,
        )
    }
}

impl FromStr for PulsedExcitationInput {
    type Err = serde_json::Error;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        serde_json::from_str(s)
    }
}
