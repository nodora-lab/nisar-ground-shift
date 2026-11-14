import asf_search as asf, json, collections
SITES = {
 "saemangeum": (126.55,35.78), "gadeokdo": (128.83,35.02), "yongin_cluster": (127.33,37.16),
 "nusantara_ikn": (116.70,-0.97), "neom_line": (35.25,28.05), "egypt_nac": (31.73,30.02),
 "port_city_colombo": (79.84,6.94),
}
out={}
for k,(x,y) in SITES.items():
    wkt=f"POINT({x} {y})"
    allp=[]
    for sn in ["NISAR_L2_GCOV_V1","NISAR_L2_GCOV_PROVISIONAL_V1","NISAR_L2_GCOV_BETA_V1"]:
        try:
            r=asf.search(shortName=sn, intersectsWith=wkt, maxResults=1000)
            allp+= [(sn,p) for p in r]
        except Exception as e: print(k,sn,"ERR",str(e)[:100])
    dates=collections.defaultdict(list)
    for sn,p in allp:
        pr=p.properties
        key=f"{pr.get('pathNumber')}/{pr.get('frameNumber')}/{pr.get('flightDirection')}"
        dates[key].append((pr['startTime'][:10], sn.split('_')[3] if sn.count('_')>3 else 'VAL', pr.get('fileName') or pr.get('sceneName'), pr.get('url'), pr.get('bytes')))
    out[k]={t:sorted(v) for t,v in dates.items()}
    print(k, "total", len(allp))
    for t,v in sorted(dates.items(), key=lambda kv:-len(kv[1])):
        print("   ",t,len(v),[d[0][5:]+d[1][0] for d in sorted(v)])
json.dump(out,open("search_result.json","w"),indent=1,default=str)
