from schedule.__init__ import Scheduler

def test_clear_all_jobs():
    scheduler = Scheduler()
    job1 = make_mock_job("job1")
    job2 = make_mock_job("job2")
    scheduler.jobs.extend([job1, job2])
    
    # Test clearing all jobs
    scheduler.clear(None)
    assert not scheduler.jobs, "All jobs should be deleted"

def test_clear_jobs_by_tag():
    scheduler = Scheduler()
    job1 = make_mock_job("job1")
    job1.tags = {"tag1"}
    job2 = make_mock_job("job2")
    job2.tags = {"tag2"}
    scheduler.jobs.extend([job1, job2])
    
    # Test clearing jobs by tag
    scheduler.clear("tag1")
    assert len(scheduler.jobs) == 1, "Only one job should remain"
    assert scheduler.jobs[0].__name__ == "job2", "Job with tag 'tag2' should be retained"

def test_clear_no_jobs():
    scheduler = Scheduler()
    
    # Test clearing when no jobs are present
    scheduler.clear(None)
    assert not scheduler.jobs, "No jobs should remain"