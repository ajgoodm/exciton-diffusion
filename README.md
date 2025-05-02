# Modelling the Diffusion of Excitons in 2D

## How to Use
This repository is composed of two halves:

1) A command line interface (CLI) to run simulations that write their output to disk.
   The simulation Rust code lives in the [`./experiment`](./experiment/) directory.
2) A command lind interface to analyze and visualize simulationt outputputs.
   The analysis/visualization Python code lives in the [`./analysis`](./analysis/)
   directory.

### Running a Simulation

To run a simulation, ensure that
[Rust is installed](https://www.rust-lang.org/tools/install). From the
[`./experiment`](./experiment/) directory, invoke the command line using cargo:

```shell
cargo run release -- ...
```

The CLI requies parameters for the excitation source as well as the excitons
being modelled. Parameters are specified as JSON and can be provided _via_ a
path to a JSON file (the output directory must exist):

```shell
cargo run --release -- \
  --exciton-parameters-input-path ../example_input/exciton_parameters.json \
  --pulsed-excitation-input-path ../example_input/pulsed_excitation_parameters.json \
  --output-directory /tmp/output
```

or as JSON string CLI inputs (the output directory must exist):
```shell
cargo run --release -- \
  --exciton-parameters-input '{"diffusivity_m2_per_s": 6.0e-6, "radiative_decay_rate_per_s": 1.0e8, "exciton_radius_m": 0.0, "annihilation_outcome": "Both"}' \
  --pulsed-excitation-input  '{"spot_fwhm_m": 0.5e-6, "repetition_rate_hz": 50.0e6, "pulse_fwhm_s": 100.0e-12, "n_excitations": 10000, "n_pulses": 1000}' \
  --output-directory /tmp/output
```

### Analyzing a result

To analyze the result of a simulation, ensure that
[uv is installed](https://docs.astral.sh/uv/getting-started/installation), ensure
that dependencies are installed:
```shell
uv run pip install -e .
```

and then invoke the analysis CLI pointing to the output of a simulation

```shell
uv run analyze show simulation-output --data-directory /tmp/output
```
