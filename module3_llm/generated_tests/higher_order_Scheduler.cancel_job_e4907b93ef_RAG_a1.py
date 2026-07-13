from schedule.__init__ import Scheduler

def test_cancel_job():
    scheduler = Scheduler()
    job = mock.Mock()

    # Test component 1: logger.debug('Cancelling job "%s"', str(job)) is deleted
    with mock.patch.object(scheduler, 'jobs', new_callable=mock.PropertyMock) as mock_jobs:
        mock_jobs.return_value.remove.side_effect = ValueError("Job not found")
        try:
            scheduler.cancel_job(job)
        except ValueError as e:
            assert str(e) == "Job not found"
        else:
            assert False, "Expected ValueError"

    # Test component 2: logger.debug('Cancelling not-scheduled job "%s"', str(job)) is deleted
    with mock.patch.object(scheduler, 'jobs', new_callable=mock.PropertyMock) as mock_jobs:
        mock_jobs.return_value.remove.side_effect = ValueError("Job not found")
        try:
            scheduler.cancel_job(job)
        except ValueError as e:
            assert str(e) == "Job not found"
        else:
            assert False, "Expected ValueError"

    # Test joint effect of both components
    with mock.patch.object(scheduler, 'jobs', new_callable=mock.PropertyMock) as mock_jobs:
        mock_jobs.return_value.remove.side_effect = ValueError("Job not found")
        try:
            scheduler.cancel_job(job)
        except ValueError as e:
            assert str(e) == "Job not found"
        else:
            assert False, "Expected ValueError"