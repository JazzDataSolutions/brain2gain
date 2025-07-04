# 🔧 DNS Fix Guide - brain2gain.mx
**Date**: 2025-07-04 17:40 UTC  
**Issue**: Domain pointing to Cloudflare with redirect loop  
**Solution**: Configure Cloudflare DNS records correctly  

## 📋 Current Situation

### ✅ **WHOIS Information Retrieved**
```
Domain: brain2gain.mx
Registrar: Registrar.eu (OpenProvider)
Created: 2024-12-18
Expires: 2025-12-18
Name Servers: 
- chance.ns.cloudflare.com
- galilea.ns.cloudflare.com
Owner: Jazz Data Solutions SA de CV
```

### 🎯 **Root Cause Identified**
- Domain uses **Cloudflare nameservers** (chance.ns.cloudflare.com, galilea.ns.cloudflare.com)
- Cloudflare DNS records NOT pointing to our VPS (5.183.9.128)
- Cloudflare causing redirect loop instead of proxying to our server

## 🔧 SOLUTION: Configure Cloudflare DNS Records

### **Step 1: Access Cloudflare Dashboard**
1. Go to https://dash.cloudflare.com/
2. Login with Cloudflare account credentials
3. Select the **brain2gain.mx** domain

### **Step 2: Update DNS Records**
Configure these A records in Cloudflare DNS:

```dns
# Required DNS Records
Type: A
Name: brain2gain.mx (or @)
IPv4: 5.183.9.128
Proxy: ⚡ Enabled (Orange Cloud)

Type: A  
Name: www
IPv4: 5.183.9.128
Proxy: ⚡ Enabled (Orange Cloud)

Type: A
Name: api
IPv4: 5.183.9.128  
Proxy: ⚡ Enabled (Orange Cloud)

Type: A
Name: admin
IPv4: 5.183.9.128
Proxy: ⚡ Enabled (Orange Cloud)
```

### **Step 3: Configure SSL/TLS Settings**
1. Go to **SSL/TLS** → **Overview**
2. Set encryption mode to: **"Full"** or **"Full (strict)"**
3. Enable **"Always Use HTTPS"**

### **Step 4: Check Origin Rules (Important)**
1. Go to **Rules** → **Origin Rules**
2. Ensure no rules are causing redirect loops
3. If any redirect rules exist, disable them temporarily

### **Step 5: Verify Settings**
1. Go to **SSL/TLS** → **Edge Certificates**
2. Ensure **"Always Use HTTPS"** is enabled
3. Check that **"Automatic HTTPS Rewrites"** is enabled

## 🚀 Alternative Solution: Point DNS Directly to Server

If Cloudflare access is not available, change nameservers:

### **Option A: Use Different DNS Provider**
1. Access domain registrar (Registrar.eu/OpenProvider)
2. Change nameservers from Cloudflare to:
   - ns1.openprovider.eu
   - ns2.openprovider.eu
   - ns3.openprovider.eu

3. Add A records directly:
```dns
brain2gain.mx     A    5.183.9.128
www.brain2gain.mx A    5.183.9.128
api.brain2gain.mx A    5.183.9.128
```

### **Option B: Use Registrar DNS**
1. Contact registrar support
2. Request DNS change to point to 5.183.9.128

## 📊 Verification Steps

After making DNS changes, test these commands:

```bash
# 1. Check DNS propagation (wait 5-60 minutes)
nslookup brain2gain.mx

# 2. Test domain access
curl -I https://brain2gain.mx

# 3. Test specific endpoints
curl https://brain2gain.mx/test
curl https://brain2gain.mx/api/v1/utils/health-check/

# 4. Check from multiple locations
# Use online tools: whatsmydns.net, dnschecker.org
```

## ⏱️ Timeline

| Step | Time Required | Description |
|------|---------------|-------------|
| **DNS Change** | 5-15 minutes | Update Cloudflare records |
| **SSL Configuration** | 2-5 minutes | Set SSL mode to Full |
| **Propagation** | 5-60 minutes | Global DNS propagation |
| **Verification** | 5-10 minutes | Test all endpoints |
| **Total** | **15-90 minutes** | Complete resolution |

## 🎯 Expected Results

After DNS fix, these should work:

```bash
✅ https://brain2gain.mx → React app loads
✅ https://brain2gain.mx/test → "Brain2Gain SSL + Reverse Proxy Working!"
✅ https://brain2gain.mx/api/v1/utils/health-check/ → JSON response
✅ https://brain2gain.mx/admin → Admin panel accessible
```

## 📞 Contact Information

**Domain Registrar**: Registrar.eu / OpenProvider  
**Support**: Contact through OpenProvider dashboard  
**Cloudflare Support**: Available if Cloudflare account accessible  

## 🔄 Fallback Plan

If Cloudflare configuration fails:
1. Disable Cloudflare proxy (gray cloud)
2. Point DNS directly to 5.183.9.128
3. Accept no CDN benefits temporarily
4. Reconfigure Cloudflare later

---

**CRITICAL**: The server is working perfectly. Only DNS configuration needs fixing.  
**Priority**: HIGH - Domain inaccessible to public  
**Impact**: Website down for external users  
**Server Status**: ✅ 100% Operational