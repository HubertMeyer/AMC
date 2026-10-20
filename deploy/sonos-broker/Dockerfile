FROM mcr.microsoft.com/dotnet/sdk:8.0-alpine AS build
WORKDIR /src

COPY Directory.Build.props ./
COPY src/AccessibleMediaController.SonosBroker/AccessibleMediaController.SonosBroker.csproj \
    src/AccessibleMediaController.SonosBroker/
RUN dotnet restore src/AccessibleMediaController.SonosBroker/AccessibleMediaController.SonosBroker.csproj

COPY src/AccessibleMediaController.SonosBroker/ \
    src/AccessibleMediaController.SonosBroker/
RUN dotnet publish \
    src/AccessibleMediaController.SonosBroker/AccessibleMediaController.SonosBroker.csproj \
    --configuration Release \
    --no-restore \
    --no-self-contained \
    --output /out \
    -p:UseAppHost=false

FROM mcr.microsoft.com/dotnet/aspnet:8.0-alpine AS runtime
WORKDIR /app
COPY --from=build /out/ ./

ENV ASPNETCORE_URLS=http://+:8080 \
    DOTNET_EnableDiagnostics=0 \
    DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1
EXPOSE 8080
USER app

ENTRYPOINT ["dotnet", "AccessibleMediaController.SonosBroker.dll"]
