from schedule.__init__ import Scheduler

def test_get_next_run_no_jobs():
    scheduler = Scheduler()
    assert scheduler.get_next_run() is None, "Should return None if no jobs are scheduled"

def test_get_next_run_with_job():
    scheduler = Scheduler()
    job = mock.Mock(next_run=datetime.datetime(2023, 10, 1, 12, 0))
    scheduler.jobs.append(job)
    assert scheduler.get_next_run() == datetime.datetime(2023, 10, 1, 12, 0), "Should return the next run time of the job"