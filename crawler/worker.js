export default {
    async fetch(request, env, ctx) {
          // GET 요청 차단
      if (request.method === "GET") return new Response("Um... You picked the wrong approach.", {status: 400});
      // https://perfectacle.github.io/2017/04/04/js-promise-param/
      
      let cf_response = new Response("Contact an administrator",{
        status: 400
      });
  // fetch config 기본값 init
      const default_ua = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36';
      const default_referer = 'https://www.google.com';
      // fetch config 기본값 init 끝 
      // header에 있는 content-type기반 body에 담긴 내용 분석
      async function readRequestBody(requests) {
        const contentType = requests.headers.get("content-type");
        if (contentType.includes("application/json")) {
          return JSON.stringify(await requests.json());
        } else {
          // Perhaps some other type of data was submitted in the form
          // like an image, or some other binary data.
          return JSON.stringify({ "error": true });
        }
      }
  
      async function fetchResultManager(response) {
        const { headers, body } = response;
        const contentType = headers.get("content-type") || "";
        if (contentType.includes("application/json")) {
          console.log(1)
          return JSON.stringify(await response.json());
        } else if (contentType.includes("application/octet-stream")) {
          console.log(2)
          return response.blob();
        } else {
          console.log(3)
          return response.text();
        }
      }
  
      const promiseFetchRequestManager = (response) => new Promise(async (resolve, reject) => {
        const { headers, status } = response;
        const contentType = headers.get("content-type") || "";
        if(status === 200) {
          if (contentType.includes("application/json")) {
            resolve(JSON.stringify(await response.json()));
          } else if (contentType.includes("application/octet-stream")) {
            resolve(response.blob());
          } else {
            resolve(response.text());
          }
        } else {
          reject(status)
        }
      })
      const url = new URL(request.url);
      if (url.pathname.startsWith('/action')) {
        console.log('v19');
        const reqBody = await readRequestBody(request);
        const inputJson = JSON.parse(reqBody);
        // content-type이 application/json인지 검사, 아닐 경우 error: true 반환되므로 error throw
        if (inputJson?.error !== true) {
          const { url, method, body, header, check_ip } = inputJson;
          /* 
          {
            "check_ip": "http://ap-northeast-2.ip.oneroom.dev:8082/check_ip",
            "method": "get",
            "url": "",
            "body": "",
            "header": {
              "Referer": "",
              "UserAgent": ""
            }
          }
          */
          const { hostname, origin } = new URL(url);
          const isUsedIpFlag = await fetch(`${check_ip}?url=${encodeURIComponent(url)}`);
          // const isUsedIpFlag = await fetch(`http://ap-northeast-2.ip.oneroom.dev:8082/check_ip?url=https%3A%2F%2Fapp.wsbox.pw/test`);
          // const isUsedIpFlag = await fetch('https://app.wsbox.pw/test')
          // const isUsedIpFlagResult = await fetchResultManager(isUsedIpFlag);
          const isUsedIpFlagResult = 
            await promiseFetchRequestManager(isUsedIpFlag)
            .then(res=>{
              const getIpUsedResult = JSON.parse(res).status;
              return getIpUsedResult;
            })
            .catch(res=>{
              cf_response = new Response(`Fetch error status: ${res}`,{
                status: res
              })
              return false;
            })
          console.log("result >> ", isUsedIpFlagResult)
          if(isUsedIpFlagResult === false) {
            cf_response = new Response("already used!", {status: 429})
          };
          if (url && isUsedIpFlagResult) {
            let cf_worker_init = {
              method: method,
              headers: {
                "Host": hostname,
                "redirect": "manual",
                "Accept": "*/*",
                "Content-Type": header["Content-Type"] || "text/html",
                "User-Agent": header?.UserAgent || default_ua,
                "Referer": header?.Referer || origin // 입력받은 referer가 있으면 사용하고 없으면 입력받은 url의 origin을 사용함
              },
            };
            if (method.toLowerCase() === 'post' && body !== "") { cf_worker_init = { ...cf_worker_init, body: body } }
  
            const cf_worker_fetch = await fetch(url, cf_worker_init);
            cf_response = await promiseFetchRequestManager(cf_worker_fetch)
              .then(res => {
                const result_content_type = cf_worker_fetch.headers.get("content-type") || "";
                const result_init = {
                  headers: {
                    "content-type": result_content_type
                  }
                }
                return new Response(res, result_init)
              })
              .catch(error => {
                console.log("error>>>>>>>>>", error)
                return new Response(error);
  
              })
            
          }
        } else {
          cf_response = new Response("Request Header Type Error",{
            status: 400
          });
        }
      } else {
        cf_response = new Response("Please use action",{
          status: 400
        });
      }
  
      return cf_response;
    },
  
  };