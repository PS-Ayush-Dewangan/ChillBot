import sys, json
sys.path.insert(0, r"C:\ChillBot")
from servers import info_server as info, fun_server as fun

print('--- INFO: get_weather_by_city(Ahmedabad) ---')
try:
    r=info.get_weather_by_city('Ahmedabad')
    print(r)
    print('JSON_OK:', isinstance(json.loads(r), dict))
except Exception as e:
    print('ERROR get_weather_by_city:', e)

print('\n--- INFO: recommend_movie(horror) ---')
try:
    r=info.recommend_movie('horror')
    print(r)
    try:
        print('JSON_OK:', isinstance(json.loads(r), dict))
    except Exception:
        print('JSON_PARSE_FAILED')
except Exception as e:
    print('ERROR recommend_movie:', e)

print('\n--- FUN: random_joke ---')
try:
    r=fun.random_joke()
    print(r)
    try:
        print('JSON_OK:', isinstance(json.loads(r), dict))
    except Exception:
        print('JSON_PARSE_FAILED')
except Exception as e:
    print('ERROR random_joke:', e)

print('\n--- FUN: motivation_quote ---')
try:
    r=fun.motivation_quote()
    print(r)
    try:
        print('JSON_OK:', isinstance(json.loads(r), dict))
    except Exception:
        print('JSON_PARSE_FAILED')
except Exception as e:
    print('ERROR motivation_quote:', e)

