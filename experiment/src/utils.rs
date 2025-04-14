use std::{path::PathBuf, sync::LazyLock};

use rand::rngs::ThreadRng;
use rand_distr::{Distribution, Uniform};
use serde::de::DeserializeOwned;
use serde_json::from_str;

static UNIFORM_ZERO_TO_PI: LazyLock<Uniform<f64>> =
    LazyLock::new(|| Uniform::new(0.0, std::f64::consts::PI).unwrap());

pub fn random_uniform_zero_to_pi(rng: &mut ThreadRng) -> f64 {
    UNIFORM_ZERO_TO_PI.sample(rng)
}

pub fn read_json_file<T: DeserializeOwned>(path: PathBuf) -> Result<T, serde_json::Error> {
    from_str(
        &std::fs::read_to_string(path.clone()).expect(&format!("failed to read file {:?}", path)),
    )
}
