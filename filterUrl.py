data = """

"""

url_list = [line.strip() for line in data.split("\n") if line.strip()]

in_scope_urls = []

out_of_scope_urls = []

keyword = "owasp"

for url in url_list:
    if keyword in url.lower():
        in_scope_urls.append(url)
    else:
        out_of_scope_urls.append(url)

print("Total URLs Processed:", len(url_list))
print("In-Scope URLs:", len(in_scope_urls))
print("Out-of-Scope URLs:", len(out_of_scope_urls))

print("In-Scope URLs:")
for url in in_scope_urls:
    print(url)
