from schedule.__init__ import Scheduler

def test_clear_with_no_tag():
    scheduler = Scheduler()
    job1 = make_mock_job("job1")
    job2 = make_mock_job("job2")
    scheduler.jobs.extend([job1, job2])

    # Simulate the deleted statement's side effect
    logger.debug = mock.Mock()

    scheduler.clear(None)

    assert not scheduler.jobs, "All jobs should be cleared"
    logger.debug.assert_called_once_with("Deleting *all* jobs")

def test_clear_with_tag():
    scheduler = Scheduler()
    job1 = make_mock_job("job1")
    job2 = make_mock_job("tagged_job")
    scheduler.jobs.extend([job1, job2])

    # Simulate the deleted statement's side effect
    logger.debug = mock.Mock()

    scheduler.clear("tagged")

    assert len(scheduler.jobs) == 1, "Only jobs with the specified tag should be cleared"
    assert scheduler.jobs[0] is job1, "Job without the specified tag should remain"
    logger.debug.assert_called_once_with('Deleting all jobs tagged "tagged"')