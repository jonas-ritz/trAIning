using Microsoft.AspNetCore.HttpOverrides;
using TrAIning.Web.Components;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container.
builder.Services.AddRazorComponents()
    .AddInteractiveServerComponents();

var app = builder.Build();

// Azure Container Apps' ingress terminates TLS and forwards to the container over plain HTTP,
// adding X-Forwarded-Proto/-For headers. Without this, ASP.NET Core sees every request as HTTP
// and UseHttpsRedirection() below can't determine a redirect target. KnownNetworks/KnownProxies
// are cleared because the immediate proxy is the Container Apps ingress, not loopback (the
// middleware's restrictive default) — safe because ingress is the only entry point into the
// container, so nothing else can spoof these headers.
var forwardedHeadersOptions = new ForwardedHeadersOptions
{
    ForwardedHeaders = ForwardedHeaders.XForwardedFor | ForwardedHeaders.XForwardedProto
};
forwardedHeadersOptions.KnownIPNetworks.Clear();
forwardedHeadersOptions.KnownProxies.Clear();
app.UseForwardedHeaders(forwardedHeadersOptions);

// Configure the HTTP request pipeline.
if (!app.Environment.IsDevelopment())
{
    app.UseExceptionHandler("/Error", createScopeForErrors: true);
    // The default HSTS value is 30 days. You may want to change this for production scenarios, see https://aka.ms/aspnetcore-hsts.
    app.UseHsts();
}
app.UseStatusCodePagesWithReExecute("/not-found", createScopeForStatusCodePages: true);
app.UseHttpsRedirection();

app.UseAntiforgery();

app.MapStaticAssets();
app.MapRazorComponents<App>()
    .AddInteractiveServerRenderMode();

app.Run();
