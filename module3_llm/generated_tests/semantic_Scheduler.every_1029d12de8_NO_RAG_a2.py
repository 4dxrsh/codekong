from schedule.__init__ import Scheduler

class TestSchedulerEvery:
    def test_correct_behavior(self):
        scheduler = Scheduler()
        job = scheduler.every(1).minutes.do(lambda: None)
        assert isinstance(job, Job), "Job should be an instance of Job"

    def test_mutated_behavior(self):
        scheduler = Scheduler()
        job = scheduler.every(1).minutes.do(lambda: None)  # This line is incorrect
        assert isinstance(job, Job), "Job should be an instance of Job"