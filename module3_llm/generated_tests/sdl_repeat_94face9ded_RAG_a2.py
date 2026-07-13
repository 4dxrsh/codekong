from schedule.__init__ import repeat

def job_fun():
    pass

@repeat(every().minute, 1, 2, "three", foo=23, bar={})
def decorated_job(*args, **kwargs):
    job_fun()

def test_repeat_decorator():
    assert 'decorated_job' in locals()