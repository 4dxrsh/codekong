from schedule.__init__ import Scheduler

def test_clear_with_tag():
    scheduler = Scheduler()
    job1 = make_mock_job("job1")
    job2 = make_mock_job("job2")
    job1.tags.add("test")
    job2.tags.add("other")
    scheduler.jobs.extend([job1, job2])

    # Simulate the deleted statement
    logger.debug('Deleting all jobs tagged "test"')

    scheduler.clear(tag="test")

    assert len(scheduler.jobs) == 1
    assert scheduler.jobs[0].__name__ == "job2"