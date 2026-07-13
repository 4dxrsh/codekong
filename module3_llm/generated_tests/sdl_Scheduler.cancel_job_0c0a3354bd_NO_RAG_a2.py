from schedule.__init__ import Scheduler

def test_cancel_job_logs_cancellation():
    scheduler = Scheduler()
    job = make_mock_job("test_job")
    scheduler.jobs.append(job)

    with mock.patch('schedule.logger.debug') as mock_debug:
        scheduler.cancel_job(job)
    
    assert mock_debug.called_once_with('Cancelling job "test_job"')