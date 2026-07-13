from schedule.__init__ import Scheduler

def test_clear_with_tag():
    scheduler = Scheduler()
    job1 = make_mock_job("job1")
    job2 = make_mock_job("job2")
    scheduler.jobs.extend([job1, job2])

    tag = "test"
    job1.tags.add(tag)
    job2.tags.add(tag)

    scheduler.clear(tag=tag)

    assert len(scheduler.jobs) == 0, "Jobs were not cleared correctly"

def test_clear_without_tag():
    scheduler = Scheduler()
    job1 = make_mock_job("job1")
    job2 = make_mock_job("job2")
    scheduler.jobs.extend([job1, job2])

    scheduler.clear()

    assert len(scheduler.jobs) == 0, "Jobs were not cleared correctly"