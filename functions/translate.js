
async function query(data, apiToken) {
    const response = await fetch(
        "https://api-inference.huggingface.co/models/praeclarum/cuneiform",
        {
            headers: { Authorization: `Bearer ${apiToken}` },
            method: "POST",
            body: JSON.stringify(data),
        }
    );
    let result = await response.text();//.json();
    for (let pair of response.headers.entries()) {
        result += "\n" + pair[0] + ': ' + pair[1];
    }
    return result;
}

export async function onRequest(context) {
    // Contents of context object
    const {
      request, // same as existing Worker API
      env, // same as existing Worker API
      params, // if filename includes [id] or [[path]]
      waitUntil, // same as ctx.waitUntil in existing Worker API
      next, // used for middleware or to fetch assets
      data, // arbitrary space for passing data between middlewares
    } = context;

    let responseText = "";

    try {

        const apiToken = env.HUGGINGFACE_API_TOKEN;

        const translationResult = await query("translate Akkadian to English: {d}a-szur_en gal_ musz-te-szer3 kisz-szat _dinger mesz_ na-din {gisz}gidri u3 a-ge-e mu-kin2 _man_-ti {d}en-lil2 be-lu _man_ gi-mir {d}a-nun-na-ki a-bu _dingir-mesz en kur kur_", apiToken);

        responseText = JSON.stringify(translationResult);

        // console.log();
    }
    catch (error) {
        // console.log(error.message);
        responseText = JSON.stringify({
            "error": `${error.name}: ${error.message}\n${error.stack}`,
        });
    }

    return new Response(responseText);
}
