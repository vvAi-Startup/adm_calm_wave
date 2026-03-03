import os
path = 'c:/Users/fatec-dsm6/Desktop/adm_calm_wave/web/app/lib/api.ts'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

refresh_logic = """
  let res; 
  try { 
      res = await fetch(`${BASE_URL}${endpoint}`, { ...options, headers }); 
  } catch (error) { 
      // Não jogue toast em todas requisições de fundo, opcional
      throw error; 
  }

  // Interceptor para Refresh Token
  if (res.status === 401 && endpoint !== "/api/auth/login" && endpoint !== "/api/auth/refresh") {
    const refreshToken = typeof window !== "undefined" ? localStorage.getItem("calmwave_refresh_token") : null;
    if (refreshToken) {
      try {
        const refreshReq = await fetch(`${BASE_URL}/api/auth/refresh`, {
          method: "POST",
          headers: { "Authorization": `Bearer ${refreshToken}` }
        });
        if (refreshReq.ok) {
          const refreshData = await refreshReq.json();
          localStorage.setItem("calmwave_token", refreshData.token);
          
          // Refaz a requisição original com o novo token
          headers["Authorization"] = `Bearer ${refreshData.token}`;
          res = await fetch(`${BASE_URL}${endpoint}`, { ...options, headers });
        } else {
          throw new Error("Refresh token expired");
        }
      } catch (err) {
        localStorage.removeItem("calmwave_token");
        localStorage.removeItem("calmwave_refresh_token");
        window.location.href = "/login";
        throw new Error("Unauthorized");
      }
    } else {
      localStorage.removeItem("calmwave_token");
      window.location.href = "/login";
      throw new Error("Unauthorized");
    }
  }

  if (res.status === 401) {
    localStorage.removeItem("calmwave_token");
    localStorage.removeItem("calmwave_refresh_token");
    window.location.href = "/login";
    throw new Error("Unauthorized");
  }
"""

old_logic = 'let res; try { res = await fetch(`${BASE_URL}${endpoint}`, { ...options, headers }); } catch (error) { toast.error("Falha de conexão com o servidor. Verifique sua internet ou tente mais tarde."); throw error; }\n\n  if (res.status === 401) {\n    localStorage.removeItem("calmwave_token");\n    window.location.href = "/login";\n    throw new Error("Unauthorized");\n  }'

text = text.replace(old_logic, refresh_logic.strip())
# Fix same logic in upload

upload_refresh_logic = """
    let res; 
    try { 
        res = await fetch(`${BASE_URL}/api/audios/upload`, {
            method: "POST",
            headers,
            body: formData,
        }); 
    } catch (error) { 
        toast.error("Falha de conexão com o servidor."); throw error; 
    }

    if (res.status === 401) {
        const refreshToken = localStorage.getItem("calmwave_refresh_token");
        if (refreshToken) {
            const refreshReq = await fetch(`${BASE_URL}/api/auth/refresh`, {
                method: "POST",
                headers: { "Authorization": `Bearer ${refreshToken}` }
            });
            if (refreshReq.ok) {
                const refreshData = await refreshReq.json();
                localStorage.setItem("calmwave_token", refreshData.token);
                headers["Authorization"] = `Bearer ${refreshData.token}`;
                res = await fetch(`${BASE_URL}/api/audios/upload`, {
                    method: "POST",
                    headers,
                    body: formData,
                });
            } else {
                localStorage.removeItem("calmwave_token");
                localStorage.removeItem("calmwave_refresh_token");
                window.location.href = "/login";
                throw new Error("Unauthorized");
            }
        } else {
            localStorage.removeItem("calmwave_token");
            localStorage.removeItem("calmwave_refresh_token");
            window.location.href = "/login";
            throw new Error("Unauthorized");
        }
    }
"""

old_upload = 'let res; try { res = await fetch(`${BASE_URL}/api/audios/upload`, {\n      method: "POST",\n      headers,\n      body: formData,\n    }); } catch (error) { toast.error("Falha de conexão com o servidor."); throw error; }\n\n    if (res.status === 401) {\n      localStorage.removeItem("calmwave_token");\n      window.location.href = "/login";\n      throw new Error("Unauthorized");\n    }'
text = text.replace(old_upload, upload_refresh_logic.strip())


# Fix types interface returns
text = text.replace(
    'fetchAPI<{ token: string; user: User }>',
    'fetchAPI<{ token: string; refresh_token?: string; user: User }>'
)


with open(path, 'w', encoding='utf-8') as f:
    f.write(text)

print("API Refresh Logic patched")
