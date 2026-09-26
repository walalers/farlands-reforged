package com.shigeo.farlandsreforged;

import com.google.common.collect.ImmutableMultimap;
import com.mojang.authlib.GameProfile;
import com.mojang.authlib.properties.Property;
import com.mojang.authlib.properties.PropertyMap;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Rotations;
import net.minecraft.core.component.DataComponents;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.decoration.ArmorStand;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.DyedItemColor;
import net.minecraft.world.item.component.ResolvableProfile;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

import java.nio.charset.StandardCharsets;
import java.util.Base64;
import java.util.Collections;
import java.util.HashMap;
import java.util.IdentityHashMap;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

/**
 * FarMan, from the Far Lands creepypastas ("Farman", "Darkness of the Farlands", "The Farlands Man"): a
 * pitch-black figure with red eyes who haunts players at the edge of the world.
 *
 * <p>He is built entirely from vanilla parts, so the mod stays server-side only and a vanilla client sees
 * him too: an invisible marker armor stand wearing black leather armor and a player head with his skin.
 * Nothing about him is ever saved on purpose; {@link #sweepStrays} removes one that a crash left behind.
 *
 * <p>A haunting escalates the longer a player stays in the Far Lands: first "FarMan joined the game", then
 * omens (cave noises, footsteps behind you, whispers in chat, redstone torches on nearby ledges), then
 * sightings of him standing far off, watching, and finally him standing right behind you. Sightings vanish
 * when you walk up to him or stare too long. Turning round to face him when he is behind you is the only
 * thing that hurts, and it only scares: a screech and a few seconds of darkness.
 */
public final class FarMan {
    /** Tag on every FarMan armor stand, so strays can be found and removed. */
    public static final String TAG = "farlandsreforged_farman";
    private static final String NAME = "FarMan";
    /**
     * Hash of FarMan's skin on textures.minecraft.net (the skin is art/farman_skin.png in the repository).
     * Empty means no skin is hosted yet, and he wears a black leather cap instead of his face.
     */
    private static final String SKIN_TEXTURE_HASH = "f9f9e13a62dbf086926be393981fbe8a12694d17e4e9b540e24b5222654d8a26";
    private static final UUID PROFILE_ID = UUID.nameUUIDFromBytes("farlandsreforged:FarMan".getBytes(StandardCharsets.UTF_8));

    private static final int FIRST_EVENT_MIN = 1200;
    private static final int FIRST_EVENT_MAX = 2400;
    private static final int EVENT_GAP_MIN = 800;
    private static final int EVENT_GAP_MAX = 2000;
    private static final int RETRY_GAP = 100;
    /** Far Lands terrain is mostly wall, so most random spots are inside solid stone. */
    private static final int SPOT_ATTEMPTS = 48;
    private static final int SWEEP_INTERVAL = 100;
    private static final int SIGHTING_LIFETIME = 900;
    private static final int SIGHTING_STARE_LIMIT = 40;
    private static final double SIGHTING_VANISH_DISTANCE = 16.0;
    private static final int BEHIND_LIFETIME = 200;
    private static final String[] WHISPERS = {
            "turn back",
            "you walked too far",
            "the world ends here",
            "i see you",
            "nobody comes back from here",
            "don't go any further",
            "this land is mine",
            "you shouldn't be here",
    };

    private static final Map<UUID, Haunt> HAUNTS = new HashMap<>();
    private static final Set<ArmorStand> ACTIVE = Collections.newSetFromMap(new IdentityHashMap<>());

    private enum Appearance { SIGHTING, BEHIND }

    private static final class Haunt {
        int cooldown = -1;
        int events;
        int sweep;
        ArmorStand figure;
        Appearance appearance;
        int figureAge;
        int stare;
        int footsteps;
        int footstepDelay;
    }

    private FarMan() {}

    /** Called once per tick for every player, on the server thread. */
    public static void tick(ServerPlayer player) {
        boolean inFarlands = player.level().dimension() == Level.OVERWORLD && FarlandsEvents.isInFarlands(player);
        Haunt haunt = inFarlands ? haunt(player) : HAUNTS.get(player.getUUID());
        if (inFarlands && ++haunt.sweep >= SWEEP_INTERVAL) {
            haunt.sweep = 0;
            sweepStrays(player);
        }
        if (!FarlandsConfig.farManEnabled() || !inFarlands || !player.isAlive() || player.isSpectator()) {
            if (haunt != null) {
                vanish(haunt);
            }
            return;
        }
        if (haunt.cooldown < 0) {
            haunt.cooldown = between(player.getRandom(), FIRST_EVENT_MIN, FIRST_EVENT_MAX);
        }

        if (haunt.footsteps > 0 && --haunt.footstepDelay <= 0) {
            footstep(player, haunt);
        }
        if (haunt.figure != null) {
            watch(player, haunt);
            return;
        }
        if (--haunt.cooldown > 0) {
            return;
        }
        boolean happened = haunt.events == 0 ? join(player) : randomEvent(player, haunt);
        if (happened) {
            haunt.events++;
            haunt.cooldown = between(player.getRandom(), EVENT_GAP_MIN, EVENT_GAP_MAX);
        } else {
            haunt.cooldown = RETRY_GAP;
        }
    }

    /** {@code /farlands farman summon}: a sighting, now. False if there was nowhere for him to stand. */
    public static boolean summon(ServerPlayer player) {
        Haunt haunt = haunt(player);
        vanish(haunt);
        return appearFarAway(player, haunt);
    }

    /** {@code /farlands farman scare}: FarMan behind the player, now. False if there was no room. */
    public static boolean scare(ServerPlayer player) {
        Haunt haunt = haunt(player);
        vanish(haunt);
        return appearBehind(player, haunt);
    }

    private static Haunt haunt(ServerPlayer player) {
        return HAUNTS.computeIfAbsent(player.getUUID(), id -> new Haunt());
    }

    private static boolean randomEvent(ServerPlayer player, Haunt haunt) {
        RandomSource random = player.getRandom();
        int sightingWeight = haunt.events >= 2 ? 4 : 0;
        int behindWeight = haunt.events >= 5 ? 1 : 0;
        int roll = random.nextInt(8 + sightingWeight + behindWeight);
        if (roll < 2) {
            return caveNoise(player);
        }
        if (roll < 4) {
            haunt.footsteps = 4;
            haunt.footstepDelay = 1;
            return true;
        }
        if (roll < 6) {
            return whisper(player);
        }
        if (roll < 8) {
            return placeTorch(player);
        }
        if (roll < 8 + sightingWeight) {
            return appearFarAway(player, haunt);
        }
        return appearBehind(player, haunt);
    }

    // ----- omens -----

    private static boolean join(ServerPlayer player) {
        player.sendSystemMessage(Component.translatable("multiplayer.player.joined", NAME).withStyle(ChatFormatting.YELLOW));
        return true;
    }

    private static boolean whisper(ServerPlayer player) {
        String line = WHISPERS[player.getRandom().nextInt(WHISPERS.length)];
        player.sendSystemMessage(Component.translatable("chat.type.text", NAME, line));
        return true;
    }

    private static boolean caveNoise(ServerPlayer player) {
        Vec3 at = behind(player, 6.0);
        player.level().playSound(null, at.x, player.getEyeY(), at.z, SoundEvents.AMBIENT_CAVE, SoundSource.AMBIENT, 1.0F, 0.8F + player.getRandom().nextFloat() * 0.3F);
        return true;
    }

    /** One of four footsteps that walk up behind the player, 10 blocks away down to 4. */
    private static void footstep(ServerPlayer player, Haunt haunt) {
        double distance = 4.0 + 2.0 * (haunt.footsteps - 1);
        haunt.footsteps--;
        haunt.footstepDelay = 9;
        Vec3 at = behind(player, distance);
        BlockPos floor = findFloor(player.level(), Mth.floor(at.x), player.getBlockY(), Mth.floor(at.z), 3, 4);
        BlockState ground = player.level().getBlockState(floor == null ? player.blockPosition().below() : floor.below());
        player.level().playSound(null, at.x, player.getY(), at.z, ground.getSoundType().getStepSound(), SoundSource.HOSTILE, 0.6F, 0.9F);
    }

    /** A redstone torch on a ledge the player can see, like the one on the cliff in "The Farlands Man". */
    private static boolean placeTorch(ServerPlayer player) {
        ServerLevel level = player.level();
        BlockState torch = Blocks.REDSTONE_TORCH.defaultBlockState();
        for (int attempt = 0; attempt < SPOT_ATTEMPTS; attempt++) {
            BlockPos pos = candidate(player, 12.0, 28.0, 60.0);
            if (pos != null && torch.canSurvive(level, pos) && canSee(player, Vec3.atCenterOf(pos))) {
                level.setBlock(pos, torch, 3);
                return true;
            }
        }
        return false;
    }

    // ----- appearances -----

    private static boolean appearFarAway(ServerPlayer player, Haunt haunt) {
        for (int attempt = 0; attempt < SPOT_ATTEMPTS; attempt++) {
            BlockPos pos = candidate(player, 24.0, 56.0, 50.0);
            if (pos == null) {
                continue;
            }
            ArmorStand figure = build(player.level(), pos);
            face(figure, player);
            if (player.hasLineOfSight(figure)) {
                return show(player, haunt, figure, Appearance.SIGHTING);
            }
        }
        return false;
    }

    private static boolean appearBehind(ServerPlayer player, Haunt haunt) {
        Vec3 at = behind(player, 2.5);
        if (!FarlandsEvents.isInFarlands(at.x, at.z)) {
            return false;
        }
        BlockPos pos = findFloor(player.level(), Mth.floor(at.x), player.getBlockY(), Mth.floor(at.z), 2, 3);
        if (pos == null) {
            return false;
        }
        ArmorStand figure = build(player.level(), pos);
        face(figure, player);
        return show(player, haunt, figure, Appearance.BEHIND);
    }

    private static boolean show(ServerPlayer player, Haunt haunt, ArmorStand figure, Appearance appearance) {
        if (!player.level().addFreshEntity(figure)) {
            return false;
        }
        haunt.figure = figure;
        haunt.appearance = appearance;
        haunt.figureAge = 0;
        haunt.stare = 0;
        ACTIVE.add(figure);
        return true;
    }

    /** Every tick while he is out: keep him turned towards the player, and decide when he goes. */
    private static void watch(ServerPlayer player, Haunt haunt) {
        ArmorStand figure = haunt.figure;
        if (figure.isRemoved() || figure.level() != player.level()) {
            vanish(haunt);
            return;
        }
        face(figure, player);
        haunt.figureAge++;
        double distance = figure.position().distanceTo(player.position());
        double facing = facing(player, figure);

        if (haunt.appearance == Appearance.SIGHTING) {
            if (facing > 0.985 && player.hasLineOfSight(figure)) {
                haunt.stare++;
            }
            if (distance < SIGHTING_VANISH_DISTANCE || haunt.stare > SIGHTING_STARE_LIMIT || haunt.figureAge > SIGHTING_LIFETIME) {
                vanish(haunt);
            }
            return;
        }

        if (facing > 0.6 && player.hasLineOfSight(figure)) {
            jumpScare(player, figure);
            vanish(haunt);
        } else if (distance > 8.0 || haunt.figureAge > BEHIND_LIFETIME) {
            vanish(haunt);
        }
    }

    private static void jumpScare(ServerPlayer player, ArmorStand figure) {
        player.level().playSound(null, figure.getX(), figure.getEyeY(), figure.getZ(), SoundEvents.ENDERMAN_STARE, SoundSource.HOSTILE, 1.0F, 0.5F);
        player.addEffect(new MobEffectInstance(MobEffects.DARKNESS, 100, 0, false, false));
        player.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, 30, 0, false, false));
    }

    private static void vanish(Haunt haunt) {
        if (haunt.figure != null) {
            ACTIVE.remove(haunt.figure);
            if (!haunt.figure.isRemoved()) {
                haunt.figure.discard();
            }
            haunt.figure = null;
        }
        haunt.footsteps = 0;
    }

    /**
     * Removes FarMan armor stands near the player that no haunting owns. They only exist if the server
     * stopped while he was out, since the world saves him along with the chunk.
     */
    private static void sweepStrays(ServerPlayer player) {
        AABB area = player.getBoundingBox().inflate(128.0);
        for (ArmorStand stand : player.level().getEntitiesOfClass(ArmorStand.class, area, stand -> stand.entityTags().contains(TAG))) {
            if (!ACTIVE.contains(stand)) {
                stand.discard();
            }
        }
    }

    // ----- the figure -----

    private static ArmorStand build(ServerLevel level, BlockPos pos) {
        ArmorStand figure = new ArmorStand(level, pos.getX() + 0.5, pos.getY(), pos.getZ() + 0.5);
        figure.addTag(TAG);
        figure.setInvisible(true);
        figure.setPermanentlyInvulnerable(true);
        figure.setSilent(true);
        figure.setNoGravity(true);
        figure.setShowArms(true);
        figure.setNoBasePlate(true);
        // A marker has no hitbox: he cannot be hit, pushed, or have his armor taken off him.
        byte flags = figure.getEntityData().get(ArmorStand.DATA_CLIENT_FLAGS);
        figure.getEntityData().set(ArmorStand.DATA_CLIENT_FLAGS, (byte) (flags | ArmorStand.CLIENT_FLAG_MARKER));
        figure.refreshDimensions();
        Rotations still = new Rotations(0.0F, 0.0F, 0.0F);
        figure.setLeftArmPose(still);
        figure.setRightArmPose(still);
        figure.setLeftLegPose(still);
        figure.setRightLegPose(still);
        figure.setItemSlot(EquipmentSlot.HEAD, head());
        figure.setItemSlot(EquipmentSlot.CHEST, black(new ItemStack(Items.LEATHER_CHESTPLATE)));
        figure.setItemSlot(EquipmentSlot.LEGS, black(new ItemStack(Items.LEATHER_LEGGINGS)));
        figure.setItemSlot(EquipmentSlot.FEET, black(new ItemStack(Items.LEATHER_BOOTS)));
        return figure;
    }

    private static ItemStack head() {
        if (SKIN_TEXTURE_HASH.isEmpty()) {
            return black(new ItemStack(Items.LEATHER_HELMET));
        }
        String textures = "{\"textures\":{\"SKIN\":{\"url\":\"http://textures.minecraft.net/texture/" + SKIN_TEXTURE_HASH + "\"}}}";
        String encoded = Base64.getEncoder().encodeToString(textures.getBytes(StandardCharsets.UTF_8));
        PropertyMap properties = new PropertyMap(ImmutableMultimap.of("textures", new Property("textures", encoded)));
        ItemStack head = new ItemStack(Items.PLAYER_HEAD);
        head.set(DataComponents.PROFILE, ResolvableProfile.createResolved(new GameProfile(PROFILE_ID, NAME, properties)));
        return head;
    }

    private static ItemStack black(ItemStack armor) {
        armor.set(DataComponents.DYED_COLOR, new DyedItemColor(0x000000));
        return armor;
    }

    /** Turns him to look straight at the player, head tilted up or down to meet their eyes. */
    private static void face(ArmorStand figure, ServerPlayer player) {
        double dx = player.getX() - figure.getX();
        double dz = player.getZ() - figure.getZ();
        double dy = player.getEyeY() - figure.getEyeY();
        float yaw = (float) Math.toDegrees(Math.atan2(dz, dx)) - 90.0F;
        float pitch = (float) -Math.toDegrees(Math.atan2(dy, Math.sqrt(dx * dx + dz * dz)));
        figure.setYRot(yaw);
        figure.setYBodyRot(yaw);
        figure.setYHeadRot(yaw);
        figure.setHeadPose(new Rotations(pitch, 0.0F, 0.0F));
    }

    // ----- geometry -----

    /** How directly the player is looking at him: 1 is dead centre, 0 is side-on, -1 is behind. */
    private static double facing(ServerPlayer player, ArmorStand figure) {
        Vec3 toFigure = figure.getEyePosition().subtract(player.getEyePosition()).normalize();
        return player.getLookAngle().dot(toFigure);
    }

    private static boolean canSee(ServerPlayer player, Vec3 target) {
        Vec3 toTarget = target.subtract(player.getEyePosition()).normalize();
        return player.getLookAngle().dot(toTarget) > 0.3;
    }

    /** A point on the horizontal line straight behind the player. */
    private static Vec3 behind(ServerPlayer player, double distance) {
        double yaw = Math.toRadians(player.getYRot());
        return new Vec3(player.getX() + Math.sin(yaw) * distance, player.getY(), player.getZ() - Math.cos(yaw) * distance);
    }

    /**
     * A standing spot within {@code spread} degrees of where the player is looking, between two distances.
     * Only inside the Far Lands: he never steps out onto normal terrain.
     */
    private static BlockPos candidate(ServerPlayer player, double near, double far, double spread) {
        RandomSource random = player.getRandom();
        double yaw = Math.toRadians(player.getYRot() + (random.nextFloat() * 2.0F - 1.0F) * spread);
        double distance = near + random.nextDouble() * (far - near);
        int x = Mth.floor(player.getX() - Math.sin(yaw) * distance);
        int z = Mth.floor(player.getZ() + Math.cos(yaw) * distance);
        if (!FarlandsEvents.isInFarlands(x + 0.5, z + 0.5)) {
            return null;
        }
        return findFloor(player.level(), x, player.getBlockY(), z, 12, 16);
    }

    /**
     * The first spot, scanning down from {@code y + up} to {@code y - down}, with two blocks of open air above
     * something to stand on. Water counts as something to stand on: he does not sink.
     */
    private static BlockPos findFloor(ServerLevel level, int x, int y, int z, int up, int down) {
        BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos(x, y + up, z);
        if (!level.isLoaded(pos)) {
            return null;
        }
        for (int i = 0; i <= up + down; i++, pos.move(0, -1, 0)) {
            if (isOpen(level, pos) && isOpen(level, pos.above()) && !level.getBlockState(pos.below()).isAir()) {
                return pos.immutable();
            }
        }
        return null;
    }

    private static boolean isOpen(ServerLevel level, BlockPos pos) {
        BlockState state = level.getBlockState(pos);
        return state.getCollisionShape(level, pos).isEmpty() && state.getFluidState().isEmpty();
    }

    private static int between(RandomSource random, int min, int max) {
        return min + random.nextInt(max - min + 1);
    }
}
