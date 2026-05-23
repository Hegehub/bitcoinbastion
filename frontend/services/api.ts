export async function apiGet<T>(path:string): Promise<T>{
  const ctl=new AbortController(); const to=setTimeout(()=>ctl.abort(),5000)
  try{const r=await fetch(path,{signal:ctl.signal}); if(!r.ok) throw new Error(`api_error_${r.status}`); const j=await r.json(); return j.data as T}
  finally{clearTimeout(to)}
}
