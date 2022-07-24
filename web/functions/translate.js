
async function query(data, apiToken) {
    const response = await fetch(
        "https://api-inference.huggingface.co/models/praeclarum/cuneiform",
        {
            headers: { Authorization: `Bearer ${apiToken}` },
            method: "POST",
            body: JSON.stringify(data),
        }
    );
    const result = await response.json();
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

    const apiToken = env.HUGGINGFACE_API_TOKEN;

    const translationResult = await query("Can you please let us know more details about your ", apiToken);
    
    console.log(JSON.stringify(translationResult));

    return new Response(JSON.stringify(translationResult));
}
