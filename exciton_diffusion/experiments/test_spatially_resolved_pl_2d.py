from exciton_diffusion.experiments.spatially_resolved_pl_2d import SpatiallyResolvedPL2DExperiment


class TestSpatiallyResolvedPL2DExperiment:
    def test_state_machine(self):
        experiment = SpatiallyResolvedPL2DExperiment()
        experiment.configure(
            start_s=1,
            end_s=2,
            time_step_s=1,
            excitation_wavelength_nm=42,
            laser_power_w=42,
        )
        experiment.run()
        experiment.report()
