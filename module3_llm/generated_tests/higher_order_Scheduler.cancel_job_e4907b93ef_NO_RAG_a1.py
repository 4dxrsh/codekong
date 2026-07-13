from schedule.__init__ import Scheduler

def test_cancel_job_original():
    scheduler = Scheduler()
    job = make_mock_job("test_job")
    scheduler.jobs.append(job)
    assert len(scheduler.jobs) == 1
    scheduler.cancel_job(job)
    assert len(scheduler.jobs) == 0

def test_cancel_job_mutated():
    scheduler = Scheduler()
    job = make_mock_job("test_job")
    scheduler.jobs.append(job)
    assert len(scheduler.jobs) == 1
    with pytest.raises(ValueError):
        scheduler.cancel_job(job)
    assert len(scheduler.jobs) == 1