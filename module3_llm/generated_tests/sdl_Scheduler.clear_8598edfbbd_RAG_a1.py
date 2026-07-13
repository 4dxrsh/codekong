from schedule.__init__ import Scheduler

def test_clear_with_tag():
    scheduler = Scheduler()
    job1 = mock.Mock(tags=["foo"])
    job2 = mock.Mock(tags=["bar"])
    scheduler.jobs.extend([job1, job2])

    scheduler.clear("foo")

    assert job1 not in scheduler.jobs
    assert job2 in scheduler.jobs

def test_clear_without_tag():
    scheduler = Scheduler()
    job1 = mock.Mock(tags=["foo"])
    job2 = mock.Mock(tags=["bar"])
    scheduler.jobs.extend([job1, job2])

    scheduler.clear()

    assert job1 not in scheduler.jobs
    assert job2 not in scheduler.jobs