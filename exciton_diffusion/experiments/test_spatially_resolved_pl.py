from exciton_diffusion.experiments.spatially_resolved_pl import SpatiallyResolvedPLExperiment


class TestSpatiallyResolvedPLExperiment:
    def test_state_machine(self):
        experiment = SpatiallyResolvedPLExperiment()
        experiment.configure()
        experiment.run()
        experiment.report()
