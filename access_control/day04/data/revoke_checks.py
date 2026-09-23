from revoke_access import revoke_assignment

print("회계 박지연이 회수하면:", revoke_assignment(
    "sora", "B전자", "jiyeon", "실험",
))
print("김도윤이 한 번 더 회수하면:", revoke_assignment(
    "sora", "B전자", "doyun", "실험",
))