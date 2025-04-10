use serde::{Deserialize, Serialize};

use crate::coord2d::Coord2D;

#[derive(Deserialize, Serialize, Clone)]
pub struct ExcitonParameters {
    pub diffusivity_m2_per_s: f64,
    pub radiative_decay_rate_per_s: f64,
    pub non_radiative_decay_rate_per_s: f64,
    pub exciton_radius_m: f64,
    pub annihilation_outcome: AnnihilationOutcome,
}

pub struct ExcitonBiography {
    pub destroyed_at_s: f64,
    pub destroyed_at_position: Coord2D,
    pub decayed_radiatively: bool,
}

impl ExcitonBiography {
    pub fn to_bytes(self) -> [u8; 24] {
        let mut result: [u8; 24] = [0; 24];
        let (time_bytes, coord_bytes) = result.split_at_mut(8);
        time_bytes.copy_from_slice(&self.destroyed_at_s.to_be_bytes());
        coord_bytes.copy_from_slice(&self.destroyed_at_position.to_bytes());

        result
    }
}

#[derive(Deserialize, Serialize, Clone)]
pub enum AnnihilationOutcome {
    Both, // both excitons are annihilated when they collide
    One,  // one exciton of the pair is randomly selected to annihilate
}
