from schedule.__init__ import Scheduler

def test_clear_all_jobs():
    scheduler = Scheduler()
    job1 = make_mock_job("job1")
    job2 = make_mock_job("job2")
    scheduler.jobs.extend([job1, job2])
    
    # Ensure the jobs are added
    assert len(scheduler.jobs) == 2
    
    # Call clear without a tag
    scheduler.clear()
    
    # Ensure all jobs are deleted
    assert not scheduler.jobs

def test_clear_jobs_by_tag():
    scheduler = Scheduler()
    job1 = make_mock_job("job1")
    job2 = make_mock_job("job2")
    job1.tags = {"tag"}
    job2.tags = set()
    scheduler.jobs.extend([job1, job2])
    
    # Ensure the jobs are added
    assert len(scheduler.jobs) == 2
    
    # Call clear with a tag
    scheduler.clear(tag="tag")
    
    # Ensure only the job without the tag is left
    assert len(scheduler.jobs) == 1
    assert scheduler.jobs[0].__name__ == "job2"