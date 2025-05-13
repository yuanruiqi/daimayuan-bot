#include <bits/stdc++.h>
using namespace std;
using i64 = long long;
constexpr int siz = 1 << 15;
char x[siz], y[siz], z[siz];
int main()
{
    freopen("data", "r", stdin);
    freopen("tab.csv", "w", stdout);
    ios::sync_with_stdio(0);
    cin.tie(0);
    map<string, map<int, int> > m;
    map<string, int> id;
    vector<string> name;
    int cnt = 0;
    for (;;)
    {
        if (!cin.getline(x, siz)) break;
        if (!x[0]) break;
        cin.getline(y, siz);
        cin.getline(z, siz);
        string a = x, b = y;
        int c = stoi(z);
        if (!id[a]) id[a] = ++cnt, name.emplace_back(a);
        m[b][id[a]] = max(m[b][id[a]], c);
    }
    cout << "#, ";
    for (int i=0;i<cnt;++i) cout << name[i] << (i == cnt - 1 ? "\n" : ", ");
    for (auto [s, p] : m)
    {
        cout << s << ", ";
        // int z = 0;
        // for (auto [x, y] : p) z += y;
        // cout << z;
        for (int i=1;i<=cnt;++i) cout << p[i] << (i == cnt ? "\n" : ", ");
        // cout << '\n';
    }
    return 0;
}