from schedule.__init__ import Scheduler

def test_clear_with_tag():
    scheduler = Scheduler()
    job1 = make_mock_job("job1")
    job2 = make_mock_job("job2")
    job1.tags.add("tag1")
    job2.tags.add("tag2")
    scheduler.jobs.extend([job1, job2])

    scheduler.clear(tag="tag1")

    assert len(scheduler.jobs) == 1
    assert "job2" in [job.__name__ for job in scheduler.jobs]