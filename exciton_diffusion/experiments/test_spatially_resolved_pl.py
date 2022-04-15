from exciton_diffusion.experiments.spatially_resolved_pl import SpatiallyResolvedPLExperiment


class TestSpatiallyResolvedPLExperiment:
    def test_state_machine(self):
        experiment = SpatiallyResolvedPLExperiment()
        experiment.configure(
            start_s=1,
            end_s=2,
            time_step_s=1,
            excitation_wavelength_nm=42,
            laser_power_w=42,
        )
        experiment.run()
        experiment.report()
