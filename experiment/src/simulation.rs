use crate::coord2d::Coord2D;
use crate::excitation_source2d::ExcitationSource2D;
use crate::exciton::{ExcitonBiography, ExcitonParameters};

pub struct Simulation2D<T: ExcitationSource2D> {
    excitation_source: T,
    exciton_parameters: ExcitonParameters,
    living_excitons: Vec<Coord2D>,
}

impl<T: ExcitationSource2D> Simulation2D<T> {
    pub fn run(self) -> Vec<ExcitonBiography> {
        vec![]
    }
}
