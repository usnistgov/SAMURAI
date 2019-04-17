#beamforming testing in julia

#3d positions structure
struct points_3d_t{T}
    x::Array{T}
    y::Array{T}
    z::Array{T}
end

#locations type. array of x,y,z values
locations_t = points_3d_t{Float64}

#spherical coordinate structure
struct spherical_coord_t{T}
    rho::T
    phi::T
    theta::T
end

#angle type
angles_t = spherical_coord{Array{Float64}}


function get_beamformed_value(locations::locations_t,angles::angles_t,freq_hz::Float64,s21_vals::Array{Complex})
    #===
     @brief get a beamformed value at a given angle from array elements at location with given s21 values
     @param[in] locations - structure containing x,y,z locations (in meters) of array elements
     @param[in] angle - structure containing a array of spherical coordinates (rho doesnt matter) of the angle to look at
     @param[in] freq_hz - frequency of the data in hz
     @param[in] s21_vals - array of complex values corresponding to recieved values at locations (x,y,z)
     @return beam steered value at the given angle
    ===#

    #first calculate the k vectors 
    c0 = 299792458; #speed of light
    k_vec = 2*pi*freq_hz/c0
    kVec = 2 * np.pi / lambdaVec
    k_dir = 
    k_loc[:] = copy(locations) #first copy the locations
    k_loc.x = loc.x
    k_loc.y = 

    for i=1:length(angles) #loop through each angle
        
    end #angles loop

end