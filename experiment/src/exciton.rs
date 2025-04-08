use serde::{Deserialize, Serialize};

use crate::coord2d::Coord2D;

#[derive(Deserialize, Serialize, Clone)]
pub struct ExcitonParameters {
    pub diffusivity_m2_per_s: f64,
    pub radiative_decay_rate_per_s: f64,
    pub non_radiative_decay_rate_per_s: f64,
    pub exciton_radius_m: f64,
}

pub struct ExcitonBiography {
    pub created_at_s: f64,
    pub destroyed_at_s: f64,
    pub destroyed_at_position: Coord2D,
    pub decayed_radiatively: bool,
}
