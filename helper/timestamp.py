from datetime import datetime, timedelta


def timestamp_to_unix_time(timestamp, timestamp_local):
    # print(timestamp)
    
    if isinstance(timestamp, str):
        if len(timestamp) >= 10:
            return timestamp
        else:
            return convert(timestamp, timestamp_local)


    elif float(timestamp)/1600000000 > 1:
        # print('UNIX FORMAT!')
        return timestamp
    else:
        return convert(timestamp, timestamp_local)

    
def convert(timestamp, timestamp_local):
    # print('')
    # print(timestamp_local)
    timestamp = str(timestamp)
    # print(timestamp)
    if timestamp != 'nan' or timestamp != '':

        # Parse the timestamp string
        timestamp_datetime_ms = None
        timestamp_datetime = None
        if '.' in timestamp:
            try:
                dot_index = str(timestamp).index('.')
                digits_before_dot = dot_index
                if digits_before_dot == 5:
                    hours = int(timestamp[:1])
                    minutes = int(timestamp[1:3])
                    seconds = int(timestamp[3:5])
                    milliseconds = int(timestamp[6:])
                elif digits_before_dot == 6:
                    hours = int(timestamp[:2])
                    minutes = int(timestamp[2:4])
                    seconds = int(timestamp[4:6])
                    milliseconds = int(timestamp[7:])
                elif digits_before_dot == 4:
                    hours = int(0)
                    minutes = int(timestamp[:2])
                    seconds = int(timestamp[2:4])
                    milliseconds = int(timestamp[5:])

                datetime_obj = datetime.fromtimestamp(timestamp_local)
                # print(datetime_obj)


                year = int(datetime_obj.year)
                month = int(datetime_obj.month)
                day = int(datetime_obj.day)
                hour = int(datetime_obj.hour)

                # timestamp_datetime_ms = timedelta(hours=hour, minutes=minutes, seconds=seconds, milliseconds=milliseconds)
                # base_datetime = datetime(year, month, day)  # Use any arbitrary date
                # timestamp_datetime = base_datetime + timestamp_datetime_ms
                
                custom_datetime = datetime(year=year, month=month, day=day, hour=hours, minute=minutes, second=seconds, microsecond=milliseconds)

                unix_time = (custom_datetime - datetime(1970, 1, 1)).total_seconds()
                # timestamp_datetime_ms = datetime.strptime(timestamp, "%H%MM%SS.%f")
                # Format '%H%MM%SS.%f' matched
            except ValueError:
                # Format '%H%MM%SS.%f' did not match
                print("Error: Time data does not match the expected format '%H%MM%SS.%f'. -> " +str(timestamp))
        else:
            try:
                timestamp_datetime = datetime.strptime(timestamp, '%H:%M:%S')
                # Format '%H:%M:%S' matched
                datetime_obj = datetime.fromtimestamp(timestamp_local)
                # print(datetime_obj)

                # Extract the year, month, and day from the datetime object
                year = datetime_obj.strftime('%Y')
                month = datetime_obj.strftime('%m')
                day = datetime_obj.strftime('%d')
                hour = datetime_obj.strftime('%H')
                # Format the date as a string in the "YYYY-MM-DD" format
                date_str = f'{year}-{month}-{day}'
                time_str = timestamp_datetime.strftime('%H:%M:%S')
                # print(time_str)
                datetime_str = f'{date_str} {time_str}'
                # print(datetime_str)
                datetime_obj = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
                # print(datetime_obj)
                unix_time = (datetime_obj - datetime(1970, 1, 1)).total_seconds()


            except ValueError:
                # Format '%H:%M:%S' did not match
                print("Error: Time data does not match the expected format '%H:%M:%S'. -> " +str(timestamp))

        return unix_time