from schedule.__init__ import Scheduler

class TestSchedulerGetNextRun:
    def test_no_jobs(self):
        scheduler = Scheduler()
        assert scheduler.get_next_run() is None

    def test_single_job_no_tag_match(self):
        scheduler = Scheduler()
        job = mock.Mock(next_run=datetime.datetime(2023, 10, 1))
        scheduler.jobs.append(job)
        assert scheduler.get_next_run(tag='other') is None

    def test_single_job_with_tag_match(self):
        scheduler = Scheduler()
        job = mock.Mock(next_run=datetime.datetime(2023, 10, 1), tags=['test'])
        scheduler.jobs.append(job)
        assert scheduler.get_next_run(tag='test') == datetime.datetime(2023, 10, 1)

    def test_multiple_jobs_with_tag_match(self):
        scheduler = Scheduler()
        job1 = mock.Mock(next_run=datetime.datetime(2023, 10, 1), tags=['test'])
        job2 = mock.Mock(next_run=datetime.datetime(2023, 10, 2), tags=['other'])
        scheduler.jobs.extend([job1, job2])
        assert scheduler.get_next_run(tag='test') == datetime.datetime(2023, 10, 1)