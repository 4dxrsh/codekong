from schedule.__init__ import Scheduler

def test_get_next_run_empty_jobs():
    scheduler = Scheduler()
    assert scheduler.get_next_run() is None, "Expected None when no jobs are scheduled"

def test_get_next_run_with_job():
    scheduler = Scheduler()
    job = make_mock_job("test_job")
    scheduler.jobs.append(job)
    job.next_run = datetime.datetime.now() + datetime.timedelta(seconds=10)
    assert scheduler.get_next_run() == job.next_run, "Expected the next run time of the scheduled job"

def test_get_next_run_with_filtered_jobs():
    scheduler = Scheduler()
    job1 = make_mock_job("test_job1")
    job2 = make_mock_job("test_job2")
    scheduler.jobs.extend([job1, job2])
    job1.next_run = datetime.datetime.now() + datetime.timedelta(seconds=10)
    job2.next_run = datetime.datetime.now() + datetime.timedelta(seconds=5)
    assert scheduler.get_next_run(tag="test_tag") == job2.next_run, "Expected the next run time of the filtered job"