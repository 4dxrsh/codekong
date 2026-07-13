from schedule.__init__ import Job

def test_decode_datetimestr_with_invalid_format():
    job = Job()
    datetime_str = "2023-10-05T14:30:00"
    formats = ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"]
    
    with mock_datetime(2023, 10, 5, 14, 30):
        result = job._decode_datetimestr(datetime_str, formats)
    
    assert result == datetime.datetime(2023, 10, 5, 14, 30), "Should return a datetime object"

def test_decode_datetimestr_with_valid_format():
    job = Job()
    datetime_str = "2023-10-05 14:30:00"
    formats = ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"]
    
    with mock_datetime(2023, 10, 5, 14, 30):
        result = job._decode_datetimestr(datetime_str, formats)
    
    assert result == datetime.datetime(2023, 10, 5, 14, 30), "Should return a datetime object"

def test_decode_datetimestr_with_no_matching_format():
    job = Job()
    datetime_str = "2023-10-05T14:30:00"
    formats = ["%Y-%m-%d %H:%M:%S"]
    
    with mock_datetime(2023, 10, 5, 14, 30):
        result = job._decode_datetimestr(datetime_str, formats)
    
    assert result is None, "Should return None if no matching format is found"