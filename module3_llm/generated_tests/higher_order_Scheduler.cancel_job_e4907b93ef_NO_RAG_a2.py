from schedule.__init__ import Scheduler

def test_cancel_job_correct():
    scheduler = Scheduler()
    job = make_mock_job("test_job")
    scheduler.jobs.append(job)
    assert job in scheduler.jobs
    scheduler.cancel_job(job)
    assert job not in scheduler.jobs

def test_cancel_job_missing_job():
    scheduler = Scheduler()
    job = make_mock_job("test_job")
    with pytest.raises(ValueError):
        scheduler.cancel_job(job)

def test_cancel_job_no_logging():
    scheduler = Scheduler()
    job = make_mock_job("test_job")
    scheduler.jobs.append(job)
    assert job in scheduler.jobs
    with mock.patch('schedule.__init__.logger.debug') as mock_debug:
        scheduler.cancel_job(job)
        mock_debug.assert_called_once_with('Cancelling job "%s"', str(job))