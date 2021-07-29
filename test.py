from datetime import datetime

time_str = '13:55'
time_object = datetime.strptime(time_str, '%H:%M').time()
print(type(time_object))
print(time_object)
