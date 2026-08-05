# Build from the repo root: docker build -f src/TrAIning.Web/Dockerfile -t training-web .
# (paths below are relative to that build context, not this file's folder)

# ---- Build stage: SDK image has the compiler, not needed at runtime ----
FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
WORKDIR /src

# In docker, every command is cached as its own layer. On a rebuild, Docker reruns a command only if
# - A) the layer before couldn't be reused from cache
# - B) that command's own content/input changed
#
# `dotnet restore` resolves and downloads this project's NuGet dependencies — the .NET
# equivalent of `pip install -r requirements.txt`. 

# By copying only the csproj first and restoring after that diretly, restoring only can not be taken 
# from cache if the csproj file has changed which is exactly the desired behavior.
# If we would copy the source first instead, and restore would come after that copy, any source-only 
# edit would cause the restore to run completely again because the command before could not be taken 
# out of the cache, forcing a full re-restore on every build regardless of whether dependencies 
# actually changed.
COPY ["src/TrAIning.Web/TrAIning.Web.csproj", "src/TrAIning.Web/"]
RUN dotnet restore "src/TrAIning.Web/TrAIning.Web.csproj"

COPY src/TrAIning.Web/ src/TrAIning.Web/
RUN dotnet publish "src/TrAIning.Web/TrAIning.Web.csproj" -c Release -o /app/publish --no-restore

# ---- Runtime stage: ASP.NET runtime only, much smaller than the SDK image ----
FROM mcr.microsoft.com/dotnet/aspnet:10.0 AS runtime
WORKDIR /app

# Azure Container Apps' ingress terminates TLS and forwards plain HTTP to the container, so
# Kestrel only needs to listen on one HTTP port here.
ENV ASPNETCORE_HTTP_PORTS=8080
EXPOSE 8080

COPY --from=build /app/publish .

ENTRYPOINT ["dotnet", "TrAIning.Web.dll"]
