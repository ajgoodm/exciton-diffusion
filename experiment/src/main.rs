use clap::Parser;
use rayon::prelude::*;

use experiment::cli_schema::{
    ExcitonParametersInput, ExistingDirectory, ExistingFilePath, PulsedExcitationInput,
};
use experiment::simulation::Simulation2D;
use experiment::utils::read_json_file;

#[derive(Parser)]
struct RunExperiment {
    #[arg(long)]
    exciton_parameters_input: Option<ExcitonParametersInput>,

    #[arg(long)]
    exciton_parameters_input_path: Option<ExistingFilePath>,

    #[arg(long)]
    pulsed_excitation_input: Option<PulsedExcitationInput>,

    #[arg(long)]
    pulsed_excitation_input_path: Option<ExistingFilePath>,

    #[arg(long)]
    output_directory: ExistingDirectory,

    #[arg(long)]
    n_processes: Option<usize>,
}

fn main() {
    let args = RunExperiment::parse();
    let exciton_parameters = match (args.exciton_parameters_input, args.exciton_parameters_input_path) {
        (Some(input), None) => input,
        (None, Some(input_path)) => read_json_file::<ExcitonParametersInput>(input_path.clone().0).expect(
            &format!("failed to parse exciton parameters at path {:?}", input_path)
        ),
        _ => panic!("Must suppply exactly one: --exciton-parameters-input XOR --exciton-parameters-input-path")
    }.params();

    let excitation_source = match (args.pulsed_excitation_input, args.pulsed_excitation_input_path) {
        (Some(input), None) => input,
        (None, Some(input_path)) => read_json_file::<PulsedExcitationInput>(input_path.clone().0).expect(
            &format!("failed to parse pulsed excitation 2D at path {:?}", input_path)
        ),
        _ => panic!("Must suppply exactly one: --pulsed-excitation-input XOR --pulsed-excitation-input-path")
    }.excitation_source();

    let simulation = Simulation2D::new(exciton_parameters, excitation_source);
    let simulation_output = if let Some(n_processes) = args.n_processes {
        rayon::ThreadPoolBuilder::new()
            .num_threads(n_processes)
            .build_global()
            .unwrap();
        let output_shards: Vec<_> = simulation
            .split(n_processes)
            .into_par_iter()
            .map(|s| s.run())
            .collect();

        panic!()
    } else {
        simulation.run()
    };

    simulation_output.write(&args.output_directory.0);
}
