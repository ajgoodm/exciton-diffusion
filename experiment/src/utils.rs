use std::{f64, sync::LazyLock};

use rand::rngs::ThreadRng;
use rand_distr::{Distribution, Uniform};

static UNIFORM_ZERO_TO_PI: LazyLock<Uniform<f64>> =
    LazyLock::new(|| Uniform::new(0.0, f64::consts::PI).unwrap());

pub fn random_uniform_zero_to_pi(rng: &mut ThreadRng) -> f64 {
    UNIFORM_ZERO_TO_PI.sample(rng)
}
