using System.Text;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Storage;
using Microsoft.IdentityModel.Tokens;


namespace polynav;

public static class Program 
{
    internal static WebApplication? App;

    private static async Task<WebApplicationBuilder> MakeBuilder(string[] args) {
        var builder = WebApplication.CreateBuilder(args);

        builder.Services.AddOpenApi();
        // builder.Services.AddDbContext<Database>();
        builder.Services.AddControllers();

        /*
        var keyValue = await UserManagement.GetJwtKey();
        if (keyValue is null)
            throw new Exception("The JWT key value is not found.");
        */

        var keyValue = Encoding.UTF8.GetBytes("placeholder");
        builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
            .AddJwtBearer(JwtBearerDefaults.AuthenticationScheme,
                options =>
                {
                    options.TokenValidationParameters = new TokenValidationParameters
                    {
                        ValidIssuer = "dotnet-backend",
                        ValidAudience = "your_audience",
                        IssuerSigningKey = new SymmetricSecurityKey(keyValue)
                    };
                });
        builder.Services.AddAuthorization();

        return builder;
    }

    public static void Main(string[] args) 
    {
        try 
        {
            var builder = MakeBuilder(args).Result;
            App = builder.Build();
        }
        catch (Exception ex) 
        {
            Console.Error.WriteLine($"Unable to open application, with error '{ex.Message}");
            return;
        }

        /*
        using (var scope = App.Services.CreateScope())
        {
            var db = scope.ServiceProvider.GetRequiredService<Database>();
            db.Database.Migrate();
        }
        */

        if (App.Environment.IsDevelopment())
        {
            App.MapOpenApi();
        }

        App.UseAuthentication();
        App.UseAuthorization();
        //App.UseHttpsRedirection();

        try 
        {
            App.Run();
        }
        catch (Exception ex) 
        {
            Console.Error.WriteLine($"Runtime exception, unexpected error '{ex}'");
        }
    }
}