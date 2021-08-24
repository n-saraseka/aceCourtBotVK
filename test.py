music_codes = ['PWR', 'JFA', 'T&T', 'AAI', 'AAI2', 'AJ', 'DD', 'SOJ']
for i in music_codes:
    request = f'-m {i}'
    ost_code = 'RND'
    if '-m' in request:
        i = 0
        while ost_code == 'RND' and i<len(music_codes):
            if music_codes[i] in request:
                ost_code = music_codes[i]
            i+=1
    print(ost_code)