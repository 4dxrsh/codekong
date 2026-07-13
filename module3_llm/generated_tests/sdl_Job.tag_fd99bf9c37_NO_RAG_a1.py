from schedule.__init__ import Job

def test_tag_with_non_hashable_tags():
    job = Job()
    tags = [1, 2, "three"]
    
    with pytest.raises(TypeError) as exc_info:
        job.tag(*tags)
    
    assert str(exc_info.value) == "Tags must be hashable"