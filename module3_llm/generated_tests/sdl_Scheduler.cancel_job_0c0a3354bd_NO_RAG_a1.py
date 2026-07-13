from schedule.__init__ import Scheduler

def test_cancel_job_logs_cancellation():
    scheduler = Scheduler()
    job = make_mock_job("test_job")
    scheduler.jobs.append(job)

    # Simulate calling cancel_job
    scheduler.cancel_job(job)

    # Assert that the job was removed from the scheduler's jobs list
    assert job not in scheduler.jobs, "Job should have been removed"

    # Assert that the cancellation log message was generated
    with mock.patch('schedule.logger.debug') as mock_debug:
        scheduler.cancel_job(job)
        mock_debug.assert_called_once_with('Cancelling job "%s"', str(job))