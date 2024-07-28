arg = "6,7,13-17,1,3,4"



result = [
    num
    for segment in arg.split(",")
    for num in (
        range(int(segment.split("-")[0]), int(segment.split("-")[1]) + 1)
        if "-" in segment
        else [int(segment)]
    )
]

print(result)
